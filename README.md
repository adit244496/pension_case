# सेवानिवृत्ती उपदान प्रणाली — Pension Case System

Automates the preparation of a **Retirement Gratuity (DCRG)** case: you enter one
employee's details once, and the system produces all 26 forms of the case file as
**Word (.docx) and PDF**, laid out like the printed originals.

Built from the reference case file `Retirment Gratuity (DCRG) case.pdf`.

---

## What it does

- **One intake, 26 documents.** Name, designation, school, dates, address and bank
  details repeat across almost every form in a DCRG case; you type them once.
- **Nothing is calculated by hand.** Qualifying service (Y-M-D), completed
  six-monthly periods, and the gratuity amount are derived from the dates and the
  last pay, in both English and Marathi words.
- **Admin-editable wording.** Every fixed sentence on every form is an editable
  text block. An admin rewords the Marathi (or English) in the browser without
  touching the layout.
- **Editable layout too.** Any form's `.docx` can be downloaded, adjusted in Word,
  and uploaded back. Previous versions are kept and can be restored.
- **One final file.** The whole case exports as a single Word document *and* a
  single PDF, in the order of the printed case file, landscape sheets included.
  Both are on the **⬇ डाउनलोड / Download** menu of each case in the list.
- **The tables do the arithmetic.** Service periods, leave days and ages are
  computed as they are typed, and a figure that disagrees with the calculation is
  flagged rather than silently replaced.
- **See what changes.** Preview any form in a browser tab with the per-case
  values shaded yellow, so it is obvious which text is filled in and which is the
  standing wording.
- **Read and correct in place.** Any form opens in a reading window inside the
  app, and its words can be changed there and saved — the layout, ruling and
  fonts are untouched. On the office machine it can also be opened in Word from
  there and the change taken straight back, with no downloading and uploading.
- **Your own forms.** Add, remove and reorder forms; the built-in ones can be
  removed and restored.
- **Bilingual interface.** Marathi and English labels appear together; the toggle
  chooses which reads first.
- **Sign-in required.** Accounts with an administrator role for template changes.

Verified against the reference case: qualifying service **16-01-00**, **32**
six-monthly periods, gratuity **₹ 2,25,600** — matching the scanned originals.

---

## Setup (Windows)

Requires **Python 3.11+**, **Node.js 22.13+** (setup.bat installs both if missing), and **Microsoft Word** (used to make
the PDFs). LibreOffice is used automatically if Word is not present.

```bat
setup.bat      :: once - installs everything, builds templates, seeds the database
start.bat      :: launches the API and the web interface
```

If an earlier copy is still running and holding the usual ports, `start.bat`
starts this one on the next free pair and says so — and opens the browser on the
port it actually used, rather than assuming 5173. **stop.bat** closes copies left
over from earlier runs (only Python and Node listening on the app's own ports;
anything else on the machine is left alone).

`start.bat` runs the app in **local desktop mode**: there is no sign-in screen,
because the machine's own user is the operator. The API still only trusts that
for requests from the same machine (127.0.0.1), so the flag cannot open up a
networked install — anything arriving over the network is asked to sign in as
usual. Remove `PENSION_LOCAL_MODE` from `start.bat` if several people share the
machine and you want the sign-in back.

`start.bat` picks the first free API port from 8000 upward and points the web
interface at it, so a leftover process on 8000 will not stop it.

Deployed on a server (see *Deploying on EC2*) the sign-in is always required:

| | |
|---|---|
| Username | `admin` |
| Password | `ChangeMe@123` (or the value of `PENSION_DEFAULT_PASSWORD`) |

Change the password from **खाते / Account** after the first sign-in — the header
shows an amber dot until you do. The API docs are at <http://127.0.0.1:8000/docs>.

<details>
<summary>Manual setup</summary>

```bash
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python build_templates.py     # writes templates/*.docx
.venv/Scripts/python -m app.seed            # schema + templates + sample case
.venv/Scripts/python -m uvicorn app.main:app --port 8000

cd ../frontend
npm install
npm run dev
```
</details>

### A shortcut on the desktop

For an office machine, the two console windows of `start.bat` are more than the
clerk needs. After `setup.bat` has run once:

```
powershell -ExecutionPolicy Bypass -File install-shortcut.ps1
```

That puts **Pension Case System** on the desktop and in the Start menu. Double
clicking it starts the system and opens it in the browser; there is no console
window and nothing to read. Roughly twenty seconds the first time, about one
second afterwards, because a second double click finds the copy already running
and simply opens the browser at it rather than starting a rival.

This is the single process arrangement: the API serves the built interface out
of `frontend/dist`, so **Node is not needed on that machine at all** and there is
no Vite server to keep alive. `stop.bat` shuts it down again.

If it cannot start, it says so in a dialog with the last few lines of
`backend/logs/server.log`, which is where the server writes.

---

## Using it

### Preparing a case

1. **प्रकरणे / Cases → + नवीन प्रकरण.** To reuse a school's letterhead, office
   addresses and treasury details, use **प्रत काढा / Duplicate** on an existing
   case instead — it copies the school and office blocks and clears the employee.
2. **तपशील / Details** — the intake fields, grouped into eight sections. Dates are
   typed as `dd-mm-yyyy`.
3. **तक्ते / Tables** — the seven repeating tables (service history, schools, pay
   sources, leave, family, nomination, breaks in service). Green **ƒx** columns
   are calculated from the dates and update as you type; the totals row at the
   foot of a table adds them up. Leave a *days* or *age* cell blank and it fills
   itself in. Type a different figure and it is kept, but the cell is flagged in
   amber with the calculated value beneath, so a disagreement is visible rather
   than buried.
4. The strip at the top of the case shows the computed service, six-monthly
   periods and gratuity as you type.
5. **कागदपत्रे / Documents → कागदपत्रे तयार करा.** Tick individual forms to
   regenerate only those; a full case takes about fifteen seconds.
6. Either use **⬇ डाउनलोड / Download** on the case list, or open the case and use the
   **संपूर्ण प्रकरण / Complete case** panel on the Documents tab. Both give the
   final outcome in the same formats:
   - **संपूर्ण Word फाईल** — every form in one .docx, each keeping its own page
     setup so the two landscape sheets stay landscape. Pictures, headers, lists
     and styles come across with the form they belong to, so a sheet edited in
     Word reaches the complete file looking as it did in Word.
   - **संपूर्ण PDF फाईल** — converted from that same Word file, so the two match
     exactly, page for page.
   Individual forms open in the reading panel described below, or download as
   Word.

### Arranging the case

The Documents tab is where a case is put in order. The **↑ ↓** arrows change
where each form prints, and the tick in the first column decides whether it goes
into the complete file — untick a form and it is left out without being deleted.
Both settings belong to that case alone and are stored on it, so they survive a
rebuild. **↺ क्रम पूर्ववत / Reset order** puts them back to the standard set.

### Reading a form without leaving the app

Clicking a form's name — or **👁 पहा / View** on its row — opens it in a reading
window over the case. The sheets appear as they print: white A4 pages centred on
a grey desk, one under the next, the way Word shows a document in print view.
Landscape sheets appear turned, exactly as they do in the printed file.

**‹ ›** or the left and right arrow keys move through the case one form at a time,
with a counter showing where you are. The page opens a little over life size at
**110%**; **− +** change that, and the percentage between them fits the sheet to
the window. The window takes the full height of the screen and is only as wide as
a sheet needs — it widens on its own for the editor below. **Esc**, the **✕**, or a click on the grey
outside closes it. Everything needed to act on the form sits along the bottom:
download the Word file, open it in Word, take back edits, or undo them.

The pages are drawn by the app itself rather than handed to the browser's PDF
plugin, so they look the same on every machine — including PCs where Acrobat has
taken over from Edge's own viewer, which used to leave the frame blank.

### Changing the words of a form, in the app

**✎ इथेच संपादित करा / Edit here** in the reading window turns the form into
boxes you can type in, laid out as the sheet is laid out: the headings and lines
of a letter one under the other, and a ruled table as a ruled table, ditto marks
and merged cells included. Change what needs changing — changed boxes turn amber
and the bar counts them — and press **✓ जतन करा / Save**. The form is remade and
the corrected page appears.

Only the *text* is written back, into the very runs it came from, so the sheet
keeps its layout to the millimetre: fonts, sizes, bold, column widths, borders,
merges and the page setup are all untouched. What it cannot do is change the
shape of a form — adding a row, moving a column, changing a border. For that,
edit the document in Word (below).

A form saved this way is marked **✎ स्वतः संपादित / Edited by hand**, listed in
the notes with who changed it and when, and left alone by later rebuilds until
it is reset — exactly as an uploaded file is.

### Editing a form by hand

Some cases need more than different words — a row added to a table, a column
widened, a note in the margin. That is a job for Word, and there are two ways
to get the file there.

**On this machine** (the app started from `start.bat`), the reading panel offers
**📝 Word मध्ये उघडा / Open in Word**, which opens the generated file in Word
itself. Edit it and save it where it is — **Ctrl+S is all there is to do**. The
app is watching the folder, so the save itself is the signal: the PDF is rebuilt
from the new file and the panel shows it, typically within a second. Nothing is
uploaded or downloaded in between, and it does not matter how the file was
opened — from this button, from Explorer, or from Word's recent files.

**↻ बदल घ्या / Pick up my edits** is still there for the one case that cannot
look after itself: a form whose PDF failed to convert is never taken in
automatically, and this asks for it by hand. Both buttons appear only in local
desktop mode; on a server the file is not on your machine, so they are hidden.

**From anywhere**, **⬆ संपादित फाईल / Edited file** takes a `.docx` you edited in
Word and uses it in place of the generated one, converting it to PDF as usual.

Such a document is marked **✎ स्वतः संपादित / Edited by hand** and is **skipped by
later rebuilds**, so an unrelated change to the case cannot quietly throw the work
away. **↺** on the row, or *Reset to generated* in the notes, discards the hand
edit and rebuilds the form from the template.

### Notes: what was changed by hand

A **स्वतः केलेले बदल / Changes made by hand** panel at the top of the Documents tab
lists everything on the case that departs from what the system would produce, so a
reviewer can see it without hunting:

- a gratuity amount entered instead of computed;
- leave days or an age that disagree with the dates;
- government resolution references edited for this case;
- documents edited by hand — in the app, in Word, or uploaded — with who and when;
- forms left out of the complete file.

Each has its reset where one applies. The panel does not appear when there is
nothing to report.

### The photograph

The **छायाचित्र / Photograph** panel on the Details tab takes the joint photograph
(JPEG or PNG, up to 8 MB). It prints inside the box on the photographs and
specimen signatures sheet. Leave it empty and the box prints blank, for a print to
be pasted in by hand as on the original. Uploading is immediate rather than part
of the save, and the forms rebuild with it.

### Keeping the forms in step with the case

Almost every field appears on several forms, so editing a detail after the
documents have been produced would leave them disagreeing with the case. Saving a
case that already has documents therefore **rebuilds every form in the
background**. The Documents tab shows *"the case has changed — the forms are being
rebuilt"* while that runs, and clears when it finishes; if it fails, the reason is
shown with a button to try again. A case that has never been generated is left
alone until you ask for it.

### Government resolution references

The circulars quoted on the covering letter are the same for every case until a
new one is issued, so they are held once under **सेटिंग्ज / Settings** and every
case follows that list — the panel shows **आपोआप / Automatic**. Editing a
reference on a case detaches that case only, and **प्रमाणित यादी वापरा / Use the
standard list** puts it back. Update the circular in Settings and every case
still following the list picks it up.

### Previewing a form

**नमुने / Templates → pick a form → नमुना पहा.** The form opens in a new browser
tab, filled with a real case. Everything shaded **yellow** is a value that changes
from case to case; everything else is the standing wording of the form. Nothing is
downloaded — close the tab when you are done.

### Changing a form's wording

**नमुने / Templates → pick a form → मजकूर संपादन.**

Each editable sentence is listed with the placeholder name it fills
(`{{ t.subject }}`). Change the Marathi (or English) text and save — the layout is
untouched. A block can itself contain `{{ }}` references, so a sentence like:

```
यांची दिनांक {{ emp.doj_unaided_f }} ते {{ svc.unaided_end_f }} अखेर विना अनुदानीत सेवा…
```

still fills itself from the case. **मूळ मजकूर परत आणा** restores the original
wording for that form.

### Changing a form's layout

**नमुने / Templates → pick a form → मांडणी.**

There are two ways to download the Word file:

- **मजकुरासह उतरवा / Download with wording** — the editable sentences are filled
  in, so the Marathi reads normally and can be corrected directly in Word. Use
  this when fixing spelling or phrasing.
- **प्लेसहोल्डरसह उतरवा / Download with placeholders** — the raw template, showing
  `{{ t.subject }}` where each editable sentence goes. Use this when you want to
  keep those sentences editable from the browser.

Either way, edit the layout in Word and upload it back. Keep the `{{ … }}` names
that carry case data — *उपलब्ध क्षेत्रे / Available placeholders* lists every name
the form can use, and **सर्व उपलब्ध क्षेत्रे दाखवा** shows everything available.
The previous file is saved and can be restored; **मूळ मांडणी परत आणा** rebuilds the
layout that ships with the system.

Any `{{ t.something }}` you add to the Word file becomes a new editable sentence
on the wording screen after upload.

### Adding, removing and reordering forms

On the **नमुने / Templates** list, each form has just **↑ ↓** to change where it
prints. Renaming and removal live behind **✎ नमुना संपादन / Edit form** at the top
of the form's own panel, so a destructive control is never one stray click away in
the list. A form you added is deleted outright; one that ships with the system is
archived and can be brought back with **काढलेले नमुने दाखवा / Show removed
forms**.

**+ नवीन नमुना / Add form** creates a form of your own — upload a Word file with
`{{ }}` placeholders, or leave the file empty to get a starter document you can
download, lay out in Word and upload back.

Forms can also be excluded from a case without removing them, using the
**वापरात / Included** checkbox.

---

## The forms

| # | Form | Lang |
|---|------|------|
| 1 | Cover sheet — Retirement Gratuity (DCRG) Case | both |
| 2 | Covering letter, school → Education Officer | mr |
| 3 | Annexure A — Departmental Data Sheet | en |
| 4 | Form 2 — letter to the Accounts Officer | en |
| 5 | Employee's own application for sanction | mr |
| 6 | Employee and bank particulars | both |
| 7 | Form I — Form for Assessing Gratuity (Part I) | en |
| 8 | Head of Office checklist + Form I account enfacement | en |
| 9 | प्रमाणपत्र — retired from a 100% aided post | mr |
| 10 | To Whomsoever It May Concern — GPF, not NPS | en |
| 11 | वचनपत्र — undertaking to refund excess payment | mr |
| 12 | Annexure I / Form 15 — application for pension & DCRG | en |
| 13 | History of Service (landscape) | en |
| 14 | Annexure II — remarks and sanction order | en |
| 15 | Photographs and specimen signatures | en |
| 16 | Declaration for pension / service gratuity | en |
| 17 | Nomination for death-cum-retirement gratuity | en |
| 18 | A declaration for pension / gratuity | en |
| 19 | Certificate — no departmental enquiry, no dues | en |
| 20 | Statement of sources of pay drawn | en |
| 21 | Last Pay Certificate | en |
| 22 | Gratuity Calculation Sheet | en |
| 23 | Statement of leave availed | en |
| 24 | Family members | en |
| 25 | Form 17 — history of breaks in service (landscape) | en |
| 26 | Service Certificate | en |

A 27th form, the **Service (FRA) Certificate + No Dues Certificate** issued by a
previous school, ships disabled because it is usually signed and supplied by that
school. Enable it under **नमुने / Templates** if you prepare it yourself.

---

## How the figures are worked out

Government convention: a period written "from A to B" includes B, so the length is
measured from A to B+1 day.

| Quantity | Rule |
|---|---|
| Service duration | `A` to `B + 1 day`, in years / months / days |
| Sums of durations | 30-day months, 360-day years |
| Net qualifying service | gross − non-qualifying + weightage |
| Six-monthly periods | `months ÷ 6`; a remainder of 3 months or more counts as one; capped at **66** |
| Retirement gratuity | `last pay ÷ 4 × periods`, capped at **₹ 20,00,000** |

The gratuity can be overridden per case (*Override gratuity amount*) when the
pension office asks for a different figure; leave it blank to compute.

To change the cap or ceiling, edit `DCRG_MAX_PERIODS` / `DCRG_CEILING` in
[`backend/app/compute.py`](backend/app/compute.py).

---

## Project layout

```
backend/
  app/
    auth.py        password hashing, signed tokens, the default administrator
    compose.py     merges the forms into one .docx, preserving page setup and
                   carrying each form's pictures, headers, lists and styles
    compute.py     date arithmetic, service length, gratuity, Marathi numerals
    context.py     case JSON -> the values templates render
    migrate.py     adds columns a database from an earlier version is missing
    preview.py     renders a form with per-case values highlighted yellow
    fields.py      bilingual intake schema (drives the React screens)
    render.py      docxtpl rendering, Jinja filters, ZIP
    pdf.py         DOCX -> PDF via Word COM, LibreOffice fallback, batching;
                   keeps one Word instance alive between conversions
    word_sync.py   takes in forms edited in Word, and the folder watcher that
                   notices the save as it happens
    generate.py    render a whole case, merge the PDFs
    models.py      Case, FormTemplate, TextBlock, GeneratedDoc
    seed.py        schema, template registration, sample case
    routers/       auth.py, cases.py, templates.py
  forms/           the 27 form layouts, in code
  docxbuild.py     python-docx helpers (fixed table widths, Devanagari runs)
  build_templates.py
  templates/       generated master .docx files
  storage/         generated documents, per case; uploads/ holds template backups
frontend/
  src/pages/       Login, CaseList, CaseEditor, Documents, TemplateAdmin
  src/components/  Field, TableEditor
  src/i18n.js      every UI string, Marathi + English
```

### Adding a field

1. Add the key to `EMPTY_CASE` in `app/context.py`.
2. Add a bilingual label to `FIELD_SECTIONS` in `app/fields.py` — the UI picks it
   up with no frontend change.
3. Reference it in a form as `{{ section.key }}`.

### Adding or changing a form

Edit the relevant module in `backend/forms/`, then:

```bash
.venv/Scripts/python build_templates.py <form_code>   # or all
.venv/Scripts/python -m app.seed                      # registers new text blocks
```

Existing admin wording is preserved; only `default_value` is refreshed.

---

## Marathi and English

Every name on these forms is written twice, once in each script. The two
directions are not equally reliable, so the interface treats them differently.

**Marathi to English is dependable**, and it is the direction to use. Devanagari
records the pronunciation, so converting it to Latin is close to mechanical. The
one judgement call — dropping the vowels a reader does not pronounce (कडलग is
"Kadlag", not "Kadlaga") — is handled, and it gets most names right on its own.

**English to Marathi is a guess.** English spelling does not record vowel length,
or which of the two "t"/"d"/"n" families is meant. "Kadlag" could be कडलग or
कडलाग; "Patil" could be पाटील or पटिल. Nothing in the input distinguishes them.

So: **just type the Marathi.** The English side fills itself in as you type — a
moment after you pause, not letter by letter — and is shown on an amber background
with an **ƒx** mark so you can see at a glance that the system wrote it rather
than a person. Correct it if the family spells the name differently; typing in the
field clears the mark, and from then on that English is yours and is never
overwritten, however much the Marathi changes. Clearing the Marathi clears an
English the system filled in, and leaves alone one that a person typed.

The other direction now fills itself in too, on the same terms: type the English
first and the Marathi appears beside it, amber and marked **ƒx**. Treat it as a
draft and read it before saving — for a name it is often wrong, because English
spelling carries neither vowel length nor which "t"/"d"/"n" family is meant. Where
the Marathi is known, type that side and let the English follow.

The **→ EN** and **→ मरा** buttons next to each paired field still do the same
conversion on demand, for a field you have already typed in by hand.

Typing is set in **Noto Sans Devanagari**, Google's Marathi face, which is carried
inside the app rather than fetched from Google — an office machine with no way out
to the internet renders it just the same. Under **सेटिंग्ज / Settings** you can
change it to any Devanagari face the machine has — Nirmala UI, Mangal, Kokila,
Aparajita and others — with a live preview. That is a screen setting only; the
font used inside the documents is separate (see *Configuration*).

Designations are *translated*, not transliterated — शिपाई is "Peon", not
"Shipai". Those come from a glossary in `backend/app/translit.py`; add to
`GLOSSARY` for terms your office uses.

Neither direction is a substitute for reading the result. A person's name is
spelled the way their family spells it, and no rule can know that.

---

## A machine without Python: the portable build

An office PC often has Windows and Word and nothing else, and no one who can
install a language runtime on it. `build_portable.bat` packs the whole
application into a folder that machine can run as it is.

Build it **here**, on the machine that has the development tools:

```bat
build_portable.bat
```

It builds the web interface, builds the form templates, and packs the API, the
templates and the interface into `dist\PensionCase` (about 96 MB). Copy that
folder to the other machine -- network share, USB stick, anything -- and run
`PensionCase.exe` there.

A console window opens, says what it is doing, and the browser opens on the case
list. There is no sign-in, as with `start.bat`, and nothing is installed: the
folder can live on the Desktop or on the stick it arrived on.

**What that machine needs**

* Windows 8.1, 10 or 11.
* Microsoft Word, 2010 or later. Word makes the PDFs there exactly as it does
  here, so the pages are identical. Without Word the Word files are still
  produced and the app says so.
* Edge or Chrome. Internet Explorer will not run the interface.
* No Python, no Node, no internet connection -- the Marathi font travels inside
  the build too.

**Where the work lives**

Everything the application writes goes in a `data` folder beside the .exe:
`pension.db`, `storage` (the Word files and PDFs) and `templates` (the forms as
that office has edited them). The templates are laid down there on the first run
and are then that office's own. Back the office up by copying `data`; move the
whole folder and the cases go with it. To upgrade, copy a new `PensionCase` over
the old one and keep the existing `data` -- new forms are added, edited wording
is left alone.

`data` can also be pointed elsewhere, at a shared drive say, with `PENSION_DATA`;
`PENSION_NO_BROWSER=1` starts it without opening a browser, for a machine where
the Task Scheduler runs it at logon. `dist\PensionCase\README.txt` says all of
this again, in the folder, for whoever sits at that machine.

**On a slow machine.** The application itself is light -- one process, SQLite,
about 80 MB of memory. The slow part is Word, which is opened to convert each
form; a full case of 26 forms takes a few minutes on old hardware the first
time. Nothing is stuck while that runs, and forms are only rebuilt when the case
actually changes.

## Deploying on EC2

The app runs as a single process: the API serves the built web interface, so
there is one service to manage. **LibreOffice replaces Word** for the PDF step on
Linux — it is installed by the scripts below along with the fonts the forms need.

A `t3.small` (2 vCPU, 2 GB) is comfortable; LibreOffice needs roughly 400 MB
while converting. Open port 80 (and 443 if you add TLS) in the security group.

### Option 1 — script on the instance

```bash
# on your machine
scp -i key.pem -r pension_case ubuntu@<ec2-host>:~/

# on the instance
sudo bash ~/pension_case/deploy/install.sh
```

It installs Python, Node, LibreOffice and the fonts, builds the templates and the
web interface, then registers a `pension` systemd service behind nginx. Pass
`SERVER_NAME=pension.example.org` to set the nginx host name.

```bash
systemctl status pension          # is it running
journalctl -u pension -f          # logs
sudo systemctl restart pension    # after changing code
```

Application code lives in `/opt/pension`; the database, documents and signing key
live in `/var/lib/pension`, which is the only directory that needs backing up.

### Option 2 — Docker

```bash
docker compose up -d --build
```

One image, LibreOffice and fonts included, data in the `pension-data` volume.

### After either

1. Open `http://<ec2-host>/` and sign in as `admin` / `ChangeMe@123` (or the value of `PENSION_DEFAULT_PASSWORD`).
2. **Change the password immediately** — the instance is on the public internet.
3. Add TLS: `sudo apt install certbot python3-certbot-nginx && sudo certbot --nginx`
4. Schedule backups: `deploy/backup.sh` copies the database (via SQLite's own
   backup, so it is never torn) and the generated documents, keeping 14 days.

### Fonts, and why the templates are rebuilt

The font names are stored inside each `.docx`, so they must exist wherever the
PDF is produced. The installer sets

```
PENSION_FONT_LATIN="Liberation Serif"        # metric-compatible with Times New Roman
PENSION_FONT_DEVANAGARI="Noto Sans Devanagari"
```

and re-runs `build_templates.py`. Liberation Serif has the same metrics as Times
New Roman, so line and page breaks land where they do on Windows. If you skip
this step LibreOffice substitutes fonts on its own and the Marathi may render as
boxes.

**Check the output after deploying.** Generate the sample case and compare a
Marathi page (the covering letter) and the two landscape sheets against the
Windows output. LibreOffice's line breaking is very close to Word's but not
identical, and a form that sits near a page boundary can spill.

### Performance

A full case is 26 Word documents plus 27 PDF conversions and takes about 60–90
seconds on a `t3.small` — slower than Word on a desktop, because LibreOffice
starts a fresh process per document. The service runs a single worker: SQLite
prefers one writer, and the conversions are CPU-bound anyway. If several clerks
prepare cases at once, move to a larger instance rather than more workers.

---

## Configuration

Both halves read a few environment variables, so the database and documents can
live on a shared drive and the ports can be moved:

| Variable | Used by | Default |
|---|---|---|
| `PENSION_DB` | API | `backend/pension.db` |
| `PENSION_STORAGE` | API | `backend/storage` |
| `PENSION_SECRET` | API | `backend/.secret` (session signing key) |
| `PENSION_FRONTEND` | API | `frontend/dist` (served directly when it exists) |
| `PENSION_ORIGINS` | API | extra CORS origins, comma-separated |
| `PENSION_FONT_LATIN` | API | `Times New Roman` (`Liberation Serif` on Linux) |
| `PENSION_FONT_DEVANAGARI` | API | `Nirmala UI` (`Noto Sans Devanagari` on Linux) |
| `PENSION_WORD_KEEPALIVE` | API | `1` — keep one Word instance between conversions; `0` starts a fresh one each time |
| `PENSION_WORD_IDLE` | API | `300` seconds of nothing to do before that instance is let go |
| `PENSION_WORD_RECYCLE` | API | `400` documents before it is replaced |
| `PENSION_API` | web | `http://127.0.0.1:8000` (API the web interface talks to) |
| `PENSION_WEB_PORT` | web | `5173` |

The two font variables are read when `build_templates.py` runs, because the names
are written into the `.docx` files; change them and rebuild the templates.

```bash
PENSION_API=http://127.0.0.1:8001 npm run dev
```

---

## Notes and limits

- **PDF conversion needs Word or LibreOffice on the machine running the API.**
  Word is used when present (Windows), LibreOffice otherwise (Linux/EC2). A
  warning appears in the header if neither is found. Word is driven one document
  at a time on a single thread that keeps the instance alive between
  conversions — starting Word costs about six seconds and converting a sheet
  about one, so the sheet rebuilt after a save in Word arrives in roughly a
  second rather than seven. A full case takes about fifteen seconds with Word
  and 60–90 seconds with LibreOffice, which has no equivalent and starts a fresh
  process per document.
- **Storage is SQLite** (`backend/pension.db`) and files on disk under
  `backend/storage/`. Fine for one office; put it behind a shared drive or move to
  PostgreSQL if several offices use one instance.
- **Sign-in is required**, with PBKDF2-hashed passwords and a signed token that
  expires after 12 hours. The signing key lives in `backend/.secret` — keep it out
  of version control (it already is) and the sessions survive a restart. There is
  no HTTPS here, so run it on an office machine or a trusted LAN; put it behind a
  reverse proxy with TLS before exposing it further. Administrators can add
  operator accounts, who may prepare cases and edit wording but not change
  layouts, add or remove forms.
- Photographs and signatures are left as blank boxes to be pasted or signed after
  printing, as in the original case file.
- **Marathi copied out of the exported PDF can differ by a character.** Word's PDF
  export writes an imperfect character map for Devanagari conjuncts, so selecting
  text in the PDF may yield e.g. `उपदाि` for `उपदान`. The printed and on-screen
  output is correct, and the Word file holds the exact text — use the .docx if you
  need to copy Marathi out. Changing the font or the export option does not help;
  it is a limitation of Word's PDF writer.
