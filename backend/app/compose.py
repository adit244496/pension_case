# -*- coding: utf-8 -*-
"""Combine the individual form documents into one complete case file.

The case has to come out as a single Word document as well as a single PDF,
laid out exactly like the printed case file -- each form starting on a new page
and the two landscape sheets (History of Service, Form 17) staying landscape.

docxcompose flattens every appended document into the master's section, which
would turn the landscape sheets portrait, so the merge is done here at the XML
level: each form keeps its own ``sectPr`` and therefore its own page size,
orientation and margins.

Moving the markup alone is not enough, though. A paragraph that shows a picture
does not carry the picture: it carries ``r:embed="rId9"``, a reference into the
relationships of the document it came from. Copy the paragraph without the part
behind it and the reference dangles -- Word calls the file corrupt and refuses
to open it, which took the complete Word and complete PDF exports down with it
for every case that had a photograph attached.

So everything a copied element points at is brought across with it: pictures,
headers and footers, hyperlinks, the numbering definitions behind a list and the
style definitions behind a paragraph, each renamed where it would collide with
something already in the master. The forms this system builds only need the
picture, but a form the clerk edits in Word can come back with any of them, and
what they see in Word has to be what comes out of the final PDF.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.opc.packuri import PackURI
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Every attribute that names a relationship -- r:embed on a picture, r:id on a
# hyperlink or a header reference, r:link on a linked image -- lives in this
# namespace, so they can be found generically rather than element by element.
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _section_properties(body):
    """The body-level <w:sectPr>, i.e. the properties of the document's last section."""
    found = body.findall(qn("w:sectPr"))
    return found[-1] if found else None


def _close_section(body, sect_pr):
    """End the current section, carrying its page setup onto the last paragraph.

    Word marks a section break by putting the section properties inside the
    ``pPr`` of the final paragraph of that section, so an existing trailing
    paragraph is reused where possible; a body that ends in a table gets the
    empty paragraph Word requires there anyway.
    """
    children = list(body)
    last = children[-1] if children else None

    if last is not None and last.tag == qn("w:p"):
        paragraph = last
    else:
        paragraph = OxmlElement("w:p")
        body.append(paragraph)

    p_pr = paragraph.find(qn("w:pPr"))
    if p_pr is None:
        p_pr = OxmlElement("w:pPr")
        paragraph.insert(0, p_pr)

    existing = p_pr.find(qn("w:sectPr"))
    if existing is not None:
        p_pr.remove(existing)
    p_pr.append(sect_pr)


# --------------------------------------------------------------------------
# carrying parts across
# --------------------------------------------------------------------------
def _unique_partname(partname: PackURI, taken: set[str]) -> PackURI:
    """A free name alongside ``partname``: image1.png -> image1-2.png."""
    stem, suffix = partname.rsplit(".", 1) if "." in str(partname) else (str(partname), "")
    tail = f".{suffix}" if suffix else ""
    n = 2
    while f"{stem}-{n}{tail}" in taken:
        n += 1
    return PackURI(f"{stem}-{n}{tail}")


def _claim_part(part, taken: set[str], seen: dict) -> None:
    """Make room in the master package for ``part`` and everything it points at.

    The part object itself is reused rather than rebuilt: relating it to the
    master puts it on the master's relationship graph, and the package writes
    out whatever that graph reaches. Only the name has to change, and only when
    the master already has a part of that name -- two forms each carrying their
    own ``/word/media/image1.png`` being the case that matters here.
    """
    key = id(part)
    if key in seen:
        return
    seen[key] = part

    if str(part.partname) in taken:
        part.partname = _unique_partname(part.partname, taken)
    taken.add(str(part.partname))

    # A header is a part that can itself hold a picture, so follow the chain.
    for rel in list(part.rels.values()):
        if not rel.is_external:
            _claim_part(rel.target_part, taken, seen)


def _remap_relationships(element, source_part, master_part, state) -> None:
    """Point every relationship reference under ``element`` at the master's copy.

    Returns nothing; the element is rewritten in place. A reference the source
    document cannot resolve is left alone -- it was already broken over there,
    and inventing a target for it would be worse than carrying it across.
    """
    cache, taken, seen = state["rids"], state["partnames"], state["parts"]
    prefix = "{%s}" % REL_NS

    for node in element.iter():
        for name, value in list(node.attrib.items()):
            if not name.startswith(prefix) or not value:
                continue
            new_id = cache.get(value)
            if new_id is None:
                rel = source_part.rels.get(value)
                if rel is None:
                    continue
                if rel.is_external:
                    new_id = master_part.relate_to(rel.target_ref, rel.reltype,
                                                   is_external=True)
                else:
                    _claim_part(rel.target_part, taken, seen)
                    new_id = master_part.relate_to(rel.target_part, rel.reltype)
                cache[value] = new_id
            node.set(name, new_id)


# --------------------------------------------------------------------------
# numbering and styles
# --------------------------------------------------------------------------
def _part_by_type(part, reltype):
    try:
        return part.part_related_by(reltype)
    except KeyError:
        return None


def _remap_numbering(element, source_doc, master_doc, state) -> None:
    """Carry the list definitions a copied list depends on into the master.

    A bulleted list is a ``w:numId`` pointing into that document's own
    numbering.xml. The master has a numbering.xml of its own with different ids,
    so without this a list the clerk added in Word comes out of the merge
    numbered like something else entirely, or not at all.
    """
    num_refs = element.findall(f".//{qn('w:numPr')}/{qn('w:numId')}")
    if not num_refs:
        return

    source_numbering = _part_by_type(source_doc.part, RT.NUMBERING)
    master_numbering = _part_by_type(master_doc.part, RT.NUMBERING)
    if source_numbering is None or master_numbering is None:
        return

    src, dst = source_numbering.element, master_numbering.element
    mapping = state["numbering"]

    def _val(node):
        return node.get(qn("w:val"))

    used = {int(_val(r)) for r in num_refs if (_val(r) or "").isdigit()}
    for num_id in sorted(used):
        if num_id in mapping:
            continue
        # w:numId is an attribute of <w:num>, but an element with w:val when it
        # appears in a paragraph's <w:numPr>.
        source_num = next(
            (n for n in src.findall(qn("w:num"))
             if n.get(qn("w:numId")) == str(num_id)), None)
        if source_num is None:
            continue

        abstract_ref = source_num.find(qn("w:abstractNumId"))
        new_abstract = None
        if abstract_ref is not None:
            source_abstract = next(
                (a for a in src.findall(qn("w:abstractNum"))
                 if a.get(qn("w:abstractNumId")) == _val(abstract_ref)), None)
            if source_abstract is not None:
                new_abstract = _next_id(dst, qn("w:abstractNum"), qn("w:abstractNumId"))
                copied = deepcopy(source_abstract)
                copied.set(qn("w:abstractNumId"), str(new_abstract))
                # An abstractNum may name a numbering style; that style is not
                # coming with it, so drop the link and keep the definition.
                for link in copied.findall(qn("w:numStyleLink")):
                    copied.remove(link)
                _insert_after_last(dst, copied, qn("w:abstractNum"))

        new_num = _next_id(dst, qn("w:num"), qn("w:numId"))
        copied_num = deepcopy(source_num)
        copied_num.set(qn("w:numId"), str(new_num))
        if new_abstract is not None:
            ref = copied_num.find(qn("w:abstractNumId"))
            if ref is not None:
                ref.set(qn("w:val"), str(new_abstract))
        dst.append(copied_num)
        mapping[num_id] = new_num

    for ref in num_refs:
        value = _val(ref)
        if (value or "").isdigit() and int(value) in mapping:
            ref.set(qn("w:val"), str(mapping[int(value)]))


def _val_of(node, tag: str) -> str | None:
    child = node.find(qn(tag))
    return None if child is None else child.get(qn("w:val"))


def _next_id(container, tag: str, attr: str) -> int:
    used = []
    for node in container.findall(tag):
        value = node.get(attr)
        if value and value.lstrip("-").isdigit():
            used.append(int(value))
    return (max(used) + 1) if used else 1


def _insert_after_last(container, element, tag: str) -> None:
    existing = container.findall(tag)
    if existing:
        existing[-1].addnext(element)
    else:
        container.insert(0, element)


def _copy_missing_styles(element, source_doc, master_doc) -> None:
    """Bring across any style a copied paragraph or run refers to by name.

    Every template this system builds shares one style sheet, so normally there
    is nothing to do. A form edited in Word is the exception: applying a heading
    from Word's own gallery adds a style definition to that file, and without it
    the heading arrives in the merge looking like body text.
    """
    try:
        source_styles = source_doc.styles.element
        master_styles = master_doc.styles.element
    except Exception:                                  # noqa: BLE001 - no style part
        return

    wanted = set()
    for tag in ("w:pStyle", "w:rStyle", "w:tblStyle"):
        for node in element.findall(f".//{qn(tag)}"):
            value = node.get(qn("w:val"))
            if value:
                wanted.add(value)
    if not wanted:
        return

    def style_ids(container):
        return {s.get(qn("w:styleId")) for s in container.findall(qn("w:style"))}

    def find(container, style_id):
        return next((s for s in container.findall(qn("w:style"))
                     if s.get(qn("w:styleId")) == style_id), None)

    have = style_ids(master_styles)
    queue = [s for s in wanted if s not in have]
    while queue:
        style_id = queue.pop()
        if style_id in have:
            continue
        source_style = find(source_styles, style_id)
        if source_style is None:
            have.add(style_id)                 # nothing to copy; stop looking
            continue
        master_styles.append(deepcopy(source_style))
        have.add(style_id)
        # basedOn / next / link name further styles this one needs.
        for tag in ("w:basedOn", "w:next", "w:link"):
            value = _val_of(source_style, tag)
            if value and value not in have:
                queue.append(value)


# --------------------------------------------------------------------------
# ids that have to be unique across the finished document
# --------------------------------------------------------------------------
def _renumber_unique_ids(body) -> None:
    """Give every drawing and bookmark in the merged body its own id.

    Each form numbers its pictures from 1 and its bookmarks from 0, so putting
    twenty-five of them in one document leaves duplicates. Word mostly copes,
    but it is exactly the kind of thing that makes it offer to repair the file.
    """
    doc_pr = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr"
    next_id = 1
    for node in body.iter(doc_pr):
        node.set("id", str(next_id))
        next_id += 1

    remap: dict[str, str] = {}
    next_bookmark = 0
    for node in body.iter(qn("w:bookmarkStart")):
        old = node.get(qn("w:id"))
        if old is not None:
            remap[old] = str(next_bookmark)
            node.set(qn("w:id"), str(next_bookmark))
            next_bookmark += 1
    for node in body.iter(qn("w:bookmarkEnd")):
        old = node.get(qn("w:id"))
        if old in remap:
            node.set(qn("w:id"), remap[old])


# --------------------------------------------------------------------------
def merge_docx(paths: list[Path], out_path: Path) -> Path:
    """Merge documents in order into one .docx, preserving each one's page setup."""
    paths = [Path(p) for p in paths if Path(p).exists()]
    if not paths:
        raise ValueError("nothing to merge")

    master = Document(str(paths[0]))
    body = master.element.body

    # Names already spoken for in the master package, so a picture arriving from
    # a later form can be told apart from the master's own.
    taken = {str(part.partname) for part in master.part.package.iter_parts()}
    parts_seen: dict = {}

    # Kept alive for the length of the merge: the master's relationships hold
    # the imported parts, but the source Documents own the lxml trees they were
    # parsed from, and letting those go would pull the parts out from under us.
    sources = []

    for path in paths[1:]:
        current = _section_properties(body)
        if current is not None:
            body.remove(current)
            _close_section(body, current)

        source = Document(str(path))
        sources.append(source)
        source_body = source.element.body

        state = {"rids": {}, "partnames": taken, "parts": parts_seen,
                 "numbering": {}}
        # Everything below is done on the source's own tree, before anything is
        # copied, so the sectPr is still attached and gets the same treatment as
        # the content -- a header reference lives in there, not in the body.
        #
        # The relationship pass has to succeed: skipping it is what leaves the
        # dangling reference Word calls corruption. Numbering and styles are
        # repairs on top of a document that already opens, so a form with a
        # numbering part this code cannot make sense of gives up that one
        # improvement rather than failing the whole case export.
        _remap_relationships(source_body, source.part, master.part, state)
        try:
            _remap_numbering(source_body, source, master, state)
        except Exception:                              # noqa: BLE001 - best effort
            pass
        try:
            _copy_missing_styles(source_body, source, master)
        except Exception:                              # noqa: BLE001 - best effort
            pass

        source_sect_pr = _section_properties(source_body)
        if source_sect_pr is not None:
            source_body.remove(source_sect_pr)

        for child in list(source_body):
            body.append(deepcopy(child))

        if source_sect_pr is not None:
            body.append(deepcopy(source_sect_pr))

    _renumber_unique_ids(body)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    master.save(str(out_path))
    return out_path
