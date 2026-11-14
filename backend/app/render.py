"""Render case documents: .docx from templates, then .pdf from those .docx files."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

import jinja2
from docxtpl import DocxTemplate

from . import compute as C
from . import pdf as pdf_engine
from .config import STORAGE_DIR, TEMPLATE_DIR
from .context import build_context

PLACEHOLDER_RE = re.compile(r"{{-?\s*([a-zA-Z_][\w.\[\]'\"]*)")

_ROMAN = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
          (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def _roman(n):
    """1 -> I, 2 -> II ... used for the numbered identification marks."""
    try:
        n = int(n)
    except (TypeError, ValueError):
        return str(n)
    out = []
    for value, numeral in _ROMAN:
        count, n = divmod(n, value)
        out.append(numeral * count)
    return "".join(out)


def xml_escape(value):
    """Escape a rendered value so it is valid inside a Word <w:t> element.

    Templates are rendered as raw document XML, so a bare "&", "<" or ">" in a
    name or an edited sentence produces malformed XML. lxml then recovers by
    dropping the broken run, and the character disappears from the document
    without any error -- "Pay & Provident Fund Unit" silently loses its "&".

    Objects that docxtpl renders as XML in their own right -- an InlineImage for
    the photograph, RichText, a Subdoc -- are passed through untouched: escaping
    their markup would turn the picture into a line of angle brackets.
    """
    if value is None:
        return ""
    if not isinstance(value, (str, int, float, bool)):
        return value
    return (str(value).replace("&", "&amp;")
                      .replace("<", "&lt;")
                      .replace(">", "&gt;"))


def _spaced(value, gap: str = " ") -> str:
    """Letter-space an identifier, the way the printed forms show them.

    Account numbers, DDO codes, PAN and Aadhaar are typed one character per box
    on the originals. Any spacing already present is normalised first.
    """
    text = "".join(str(value or "").split())
    return gap.join(text)


def jinja_env() -> jinja2.Environment:
    """Jinja environment shared by every template, with the form filters."""
    env = jinja2.Environment(undefined=jinja2.ChainableUndefined)
    env.finalize = xml_escape
    env.filters.update({
        "dt": C.fmt_date,                 # 03-03-1964
        "dt_mr": C.fmt_date_dev,          # Devanagari digits
        "dt_long": C.fmt_date_long_en,    # 24 August, 2023
        "dt_mr_long": C.fmt_date_mr,
        "dev": C.to_dev,
        "money": C.rupees,                # 2,25,600/-
        "inr": C.indian_number,           # 2,25,600
        "words_en": C.amount_words_en,
        "words_mr": C.amount_words_mr,
        "ordinal": C.ordinal_en,
        "upper2": lambda v: str(v or "").upper(),
        "blank": lambda v, dash="---": v if str(v or "").strip() else dash,
        "roman": _roman,
        "spaced": _spaced,          # 5401001878 -> 5 4 0 1 0 0 1 8 7 8
    })
    return env


def template_path(docx_name: str) -> Path:
    return TEMPLATE_DIR / docx_name


def case_dir(case_no: str) -> Path:
    safe = re.sub(r"[^\w.-]+", "_", case_no or "case")
    path = STORAGE_DIR / safe
    path.mkdir(parents=True, exist_ok=True)
    return path


def _slug(text: str) -> str:
    return re.sub(r"[^\w]+", "_", str(text or "")).strip("_")[:60] or "doc"


def close_empty_cells(document) -> int:
    """Put a paragraph back into any table cell rendering emptied. Returns how many.

    A cell whose whole content is a ``{%p for ... %}`` loop -- the identification
    marks, a nominee's alternates -- loses every one of its paragraphs when the
    list is empty, because that tag takes its own paragraph with it. Word will
    not open a ``<w:tc>`` with no paragraph in it: it reports "the file appears
    to be corrupted" and refuses, which took down the form's PDF and, through
    the merge, the complete case file with it. An employee with no
    identification marks recorded was enough to trigger it.

    The same rule covers a cell that ends in a nested table, which OOXML also
    requires to be followed by a paragraph.
    """
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    fixed = 0
    for cell in document.element.body.iter(qn("w:tc")):
        blocks = [child for child in cell
                  if child.tag in (qn("w:p"), qn("w:tbl"))]
        if not blocks or blocks[-1].tag == qn("w:tbl"):
            cell.append(OxmlElement("w:p"))
            fixed += 1
    return fixed


def render_docx(docx_name: str, context: dict, out_path: Path,
                env: jinja2.Environment | None = None,
                images: dict | None = None) -> Path:
    """Fill one template and write the resulting .docx.

    ``images`` maps a context name to (filename, width_cm); each is resolved
    against the loaded template, because an InlineImage has to be attached to
    the document it will live in.
    """
    src = template_path(docx_name)
    if not src.exists():
        raise FileNotFoundError(f"template missing: {docx_name}")
    doc = DocxTemplate(str(src))
    for name, (case_no, filename, width) in (images or {}).items():
        context[name] = photo_for(doc, case_no, filename, width)
    doc.render(context, env or jinja_env())
    close_empty_cells(doc.docx)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
    return out_path


def resolve_blocks(blocks: dict, ctx: dict, env: jinja2.Environment) -> dict:
    """Render the admin's text blocks against the case context.

    Blocks are editable sentences, and several of them legitimately contain
    placeholders of their own (a Marathi paragraph that names the retirement
    date, say), so each value is itself run through Jinja before it reaches
    the document.
    """
    out = {}
    for key, value in (blocks or {}).items():
        text = str(value or "")
        if "{{" in text or "{%" in text:
            try:
                text = env.from_string(text).render(ctx)
            except jinja2.TemplateError:
                pass                       # leave the raw text; the admin will see it
        out[key] = text
    return out


def render_form(case, template, blocks: dict, *, make_pdf: bool = True,
                index: int | None = None, preview: bool = False,
                out_dir: Path | None = None) -> dict:
    """Render one form for one case; returns paths and any PDF error.

    With ``preview``, values coming from the case data are highlighted yellow so
    the admin can see at a glance which text changes for each employee.
    """
    from .preview import Static, highlight_marked, preview_env

    base_env = jinja_env()
    env = preview_env(base_env) if preview else base_env
    doc_meta = {"code": template.code, "title_en": template.title_en,
                "title_mr": template.title_mr, "order_no": template.order_no}
    ctx = build_context(case.data, blocks={}, doc_meta=doc_meta)
    resolved = resolve_blocks(blocks, ctx, env)
    # The standing wording of the form is never highlighted, only the values in it.
    ctx["t"] = {k: Static(v) for k, v in resolved.items()} if preview else resolved

    order = index if index is not None else template.order_no
    stem = f"{order:02d}_{_slug(template.code)}"
    if preview:
        stem = f"preview_{_slug(template.code)}"
    out_dir = out_dir or case_dir(case.case_no)

    photo = (case.data or {}).get("employee", {}).get("photo", "")
    docx_path = render_docx(
        template.docx_name, ctx, out_dir / f"{stem}.docx", env,
        images={"photo": (case.case_no, photo, 5.0)},
    )
    if preview:
        highlight_marked(docx_path)

    pdf_path, error = "", ""
    if make_pdf:
        try:
            pdf_path = str(pdf_engine.docx_to_pdf(docx_path, out_dir / f"{stem}.pdf"))
            pdf_engine.rotate_landscape_pages(Path(pdf_path))
        except Exception as exc:                      # noqa: BLE001 - surfaced to the UI
            error = str(exc)

    return {"docx_path": str(docx_path), "pdf_path": pdf_path, "pdf_error": error}


def placeholders_in(docx_name: str) -> list[str]:
    """List the {{ ... }} names a template uses -- shown on the admin screen."""
    src = template_path(docx_name)
    if not src.exists():
        return []
    try:
        doc = DocxTemplate(str(src))
        doc.init_docx()                 # docxtpl loads the document lazily
        xml = doc.patch_xml(doc.get_xml())
    except Exception:                   # noqa: BLE001 - a bad upload must not 500
        return []
    found = {m.group(1) for m in PLACEHOLDER_RE.finditer(xml)}
    return sorted(found)


def build_zip(paths: list[Path], out_path: Path, arc_prefix: str = "") -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in paths:
            path = Path(path)
            if path.exists():
                zf.write(path, arcname=str(Path(arc_prefix) / path.name))
    return out_path


BLOCK_TAG_RE = re.compile(r"\{\{-?\s*t\.(\w+)\s*(?:\|[^}]*?)?-?\}\}")


def resolve_text_blocks(docx_name: str, blocks: dict, out_path: Path) -> Path:
    """Write a copy of a template with the editable wording filled in.

    An admin correcting Marathi wants to see the actual sentence in Word, not
    ``{{ t.subject }}``. This substitutes the text blocks and leaves the
    case-data placeholders alone, so the file can be edited and uploaded back.
    """
    from docx import Document

    source = template_path(docx_name)
    if not source.exists():
        raise FileNotFoundError(f"template missing: {docx_name}")
    document = Document(str(source))

    def substitute(match):
        return str(blocks.get(match.group(1), match.group(0)))

    for paragraph in _all_paragraphs(document):
        if "{{" not in paragraph.text or "t." not in paragraph.text:
            continue
        for run in paragraph.runs:
            if BLOCK_TAG_RE.search(run.text):
                run.text = BLOCK_TAG_RE.sub(substitute, run.text)
        # A tag split across runs by Word survives the per-run pass untouched;
        # rebuild the whole paragraph in that case.
        if BLOCK_TAG_RE.search(paragraph.text):
            merged = BLOCK_TAG_RE.sub(substitute, paragraph.text)
            for extra in paragraph.runs[1:]:
                extra._element.getparent().remove(extra._element)
            if paragraph.runs:
                paragraph.runs[0].text = merged
            else:
                paragraph.add_run(merged)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(out_path))
    return out_path


def _all_paragraphs(container):
    for paragraph in container.paragraphs:
        yield paragraph
    for table in container.tables:
        for row in table.rows:
            for cell in row.cells:
                yield from _all_paragraphs(cell)


def case_photo_path(case_no: str, filename: str) -> Path | None:
    """Absolute path of a photo uploaded for a case, if it is still there."""
    if not filename:
        return None
    candidate = (case_dir(case_no) / "photos" / Path(filename).name)
    return candidate if candidate.exists() else None


def readable_image(path: Path) -> bool:
    """Whether Word will be able to place this file as a picture."""
    from docx.image.image import Image

    try:
        Image.from_blob(Path(path).read_bytes())
        return True
    except Exception:                       # noqa: BLE001 - not an image we can use
        return False


def photo_for(doc: DocxTemplate, case_no: str, filename: str, width_cm: float = 5.0):
    """An InlineImage for the photographs sheet, or '' when none was uploaded.

    Returning an empty string leaves the pasted-photograph box empty, which is
    what the printed form expects when the picture is attached by hand.

    The file is read here rather than left to the render, because an InlineImage
    does not touch it until the document is being written out -- by which point
    a picture that cannot be read is no longer "no photograph", it is the whole
    form failing with a decoding error the clerk cannot act on.
    """
    from docx.shared import Cm
    from docxtpl import InlineImage

    path = case_photo_path(case_no, filename)
    if path is None or not readable_image(path):
        return ""
    try:
        return InlineImage(doc, str(path), width=Cm(width_cm))
    except Exception:                       # noqa: BLE001 - a bad image must not stop the case
        return ""
