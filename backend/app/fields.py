# -*- coding: utf-8 -*-
"""Bilingual description of the case intake form.

The React app renders its screens from this, so a new field needs adding in one
place only.  Every label carries both an English and a Marathi form; the UI
shows them together (Marathi above, English below) rather than making the user
pick a language.

field types: text | textarea | date | number | select | list
"""
from __future__ import annotations

FIELD_SECTIONS = [
    {
        "key": "meta",
        "title_en": "Case & letter details",
        "title_mr": "प्रकरण व पत्र तपशील",
        "fields": [
            ("case_no", "Case number", "प्रकरण क्रमांक", "text", None),
            ("letter_ref_no", "Outward / reference number", "जावक क्रमांक", "text", None),
            ("letter_date", "Letter date", "पत्राचा दिनांक", "date", None),
            ("application_date", "Date of application", "अर्जाचा दिनांक", "date", None),
            ("place", "Place (English)", "ठिकाण (इंग्रजी)", "text", None),
            ("place_mr", "Place (Marathi)", "ठिकाण (मराठी)", "text", None),
            ("class_of_pension", "Class of pension", "निवृत्तीवेतनाचा प्रकार", "select",
             ["Superannuation", "Voluntary", "Premature", "Invalid", "Compulsory",
              "Surplus", "Absorption", "Abolition", "Removal"]),
        ],
    },
    {
        "key": "school",
        "title_en": "School / institution",
        "title_mr": "शाळा / संस्था",
        "fields": [
            ("society_line_mr", "Society line (Marathi)", "संस्थेचे नाव (मराठी)", "textarea", None),
            ("society_line_en", "Society line (English)", "संस्थेचे नाव (इंग्रजी)", "textarea", None),
            ("name_mr", "School name (Marathi)", "शाळेचे नाव (मराठी)", "textarea", None),
            ("name_en", "School name (English)", "शाळेचे नाव (इंग्रजी)", "textarea", None),
            ("taluka_mr", "Taluka (Marathi)", "तालुका (मराठी)", "text", None),
            ("taluka_en", "Taluka (English)", "तालुका (इंग्रजी)", "text", None),
            ("district_mr", "District (Marathi)", "जिल्हा (मराठी)", "text", None),
            ("district_en", "District (English)", "जिल्हा (इंग्रजी)", "text", None),
            ("pin", "PIN code", "पिन कोड", "text", None),
            ("ddo_code", "10 digit DDO code", "१० अंकी डीडीओ कोड", "text", None),
            ("department_en", "Department (English)", "विभाग (इंग्रजी)", "text", None),
            ("department_mr", "Department (Marathi)", "विभाग (मराठी)", "text", None),
            ("hm_name_mr", "Head master name (Marathi)", "मुख्याध्यापकाचे नाव (मराठी)", "text", None),
            ("hm_name_en", "Head master name (English)", "मुख्याध्यापकाचे नाव (इंग्रजी)", "text", None),
        ],
    },
    {
        "key": "office",
        "title_en": "Addressee offices",
        "title_mr": "संबंधित कार्यालये",
        "fields": [
            ("addressee_mr", "Addressee block (Marathi)", "पत्र ज्यांना (मराठी)", "textarea", None),
            ("addressee_en", "Addressee block (English)", "पत्र ज्यांना (इंग्रजी)", "textarea", None),
            ("eo_designation_mr", "Education officer designation (Marathi)",
             "शिक्षणाधिकारी पदनाम (मराठी)", "text", None),
            ("eo_designation_en", "Education officer designation (English)",
             "शिक्षणाधिकारी पदनाम (इंग्रजी)", "text", None),
            ("zp_district_en", "Zilla Parishad district", "जिल्हा परिषद जिल्हा", "text", None),
            ("treasury", "Treasury for payment", "कोषागार", "text", None),
            ("to_pension", "T.O. for pension", "निवृत्तीवेतन कोषागार", "text", None),
            ("to_dcrg", "T.O. for DCRG", "उपदान कोषागार", "text", None),
            ("ag_office_en", "Accountant General office", "महालेखापाल कार्यालय", "textarea", None),
        ],
    },
    {
        "key": "employee",
        "title_en": "Employee details",
        "title_mr": "कर्मचारी तपशील",
        "fields": [
            ("name_mr", "Name (Marathi)", "सेवकाचे नाव (मराठी)", "text", None),
            ("name_en", "Name (English)", "सेवकाचे नाव (इंग्रजी)", "text", None),
            ("father_name_mr", "Father's name (Marathi)", "वडिलांचे नाव (मराठी)", "text", None),
            ("father_name_en", "Father's name (English)", "वडिलांचे नाव (इंग्रजी)", "text", None),
            ("mother_name_en", "Mother's name", "आईचे नाव", "text", None),
            ("spouse_name_en", "Spouse name (English)", "पती/पत्नीचे नाव (इंग्रजी)", "text", None),
            ("spouse_name_mr", "Spouse name (Marathi)", "पती/पत्नीचे नाव (मराठी)", "text", None),
            ("designation_mr", "Designation (Marathi)", "हुद्दा (मराठी)", "text", None),
            ("designation_en", "Designation (English)", "हुद्दा (इंग्रजी)", "text", None),
            ("group_class", "Group / class", "गट / वर्ग", "text", None),
            ("sex", "Sex", "लिंग", "select", ["Male", "Female", "Other"]),
            ("religion_caste", "Religion and caste", "धर्म व जात", "text", None),
            ("nationality", "Nationality", "राष्ट्रीयत्व", "text", None),
            ("dob", "Date of birth", "जन्मतारीख", "date", None),
            ("doj_unaided", "Date of joining (un-aided)", "नियुक्ती दिनांक (विनाअनुदानित)",
             "date", None),
            ("doj_aided", "Date of joining (100% aided)", "नियुक्ती दिनांक (१००% अनुदानित)",
             "date", None),
            ("dor", "Date of retirement", "सेवानिवृत्ती दिनांक", "date", None),
            ("mobile", "Mobile number", "मोबाईल नंबर", "text", None),
            ("email", "Email", "ई-मेल", "text", None),
            ("aadhaar", "Aadhaar number", "आधार नंबर", "text", None),
            ("pan", "PAN number", "पॅन नंबर", "text", None),
            ("addr_at", "Address - At (English)", "पत्ता - मु. (इंग्रजी)", "text", None),
            ("addr_post", "Address - Post (English)", "पत्ता - पोस्ट (इंग्रजी)", "text", None),
            ("addr_taluka", "Address - Taluka (English)", "पत्ता - तालुका (इंग्रजी)", "text", None),
            ("addr_district", "Address - District (English)", "पत्ता - जिल्हा (इंग्रजी)",
             "text", None),
            ("addr_pin", "Address - PIN", "पत्ता - पिन", "text", None),
            ("addr_state", "Address - State", "पत्ता - राज्य", "text", None),
            ("addr_at_mr", "Address - At (Marathi)", "पत्ता - मु. (मराठी)", "text", None),
            ("addr_post_mr", "Address - Post (Marathi)", "पत्ता - पोस्ट (मराठी)", "text", None),
            ("addr_taluka_mr", "Address - Taluka (Marathi)", "पत्ता - तालुका (मराठी)", "text", None),
            ("addr_district_mr", "Address - District (Marathi)", "पत्ता - जिल्हा (मराठी)",
             "text", None),
            ("height", "Height", "उंची", "text", None),
            ("identification_marks", "Identification marks", "ओळखीच्या खुणा", "list", None),
            ("substantive", "Substantive status", "स्थायी स्थिती", "text", None),
        ],
    },
    {
        "key": "pay",
        "title_en": "Pay particulars",
        "title_mr": "वेतन तपशील",
        "fields": [
            ("level", "Level of pay in pay matrix", "वेतन स्तर", "text", None),
            ("matrix", "Pay matrix range", "वेतन मॅट्रिक्स", "text", None),
            ("basic", "Basic pay", "मूळ वेतन", "number", None),
            ("grade_pay", "Grade pay", "ग्रेड वेतन", "number", None),
            ("last_pay_for_gratuity", "Last pay for gratuity", "उपदानासाठी अंतिम वेतन",
             "number", None),
            ("da_pct", "DA percentage", "महागाई भत्ता टक्के", "number", None),
            ("da_amt", "DA amount", "महागाई भत्ता रक्कम", "number", None),
            ("hra_pct", "HRA percentage", "घरभाडे भत्ता टक्के", "number", None),
            ("hra_amt", "HRA amount", "घरभाडे भत्ता रक्कम", "number", None),
            ("travel_allowance", "Travel allowance", "प्रवास भत्ता", "number", None),
            ("other_allowance", "Other allowance", "इतर भत्ता", "number", None),
            ("total_salary", "Total salary", "एकूण वेतन", "number", None),
            ("paid_upto", "Pay drawn up to", "वेतन अदा केल्याचा महिना", "text", None),
            ("average_emoluments", "Average emoluments", "सरासरी वेतन", "number", None),
            ("npa", "Non-practicing allowance", "एन.पी.ए.", "number", None),
        ],
    },
    {
        "key": "bank",
        "title_en": "Bank and GPF",
        "title_mr": "बँक व भ.नि.नि.",
        "fields": [
            ("name", "Bank name", "बँकेचे नाव", "text", None),
            ("branch", "Branch", "शाखा", "text", None),
            ("branch_address", "Branch address", "शाखेचा पत्ता", "textarea", None),
            ("account_no", "Account number", "खाते क्रमांक", "text", None),
            ("micr", "MICR code", "एम.आय.सी.आर. कोड", "text", None),
            ("ifsc", "IFSC code", "आय.एफ.एस.सी. कोड", "text", None),
            ("gpf_no", "GPF account number", "भ.नि.नि. खाते क्रमांक", "text", None),
        ],
    },
    {
        "key": "service",
        "title_en": "Service & gratuity",
        "title_mr": "सेवा व उपदान",
        "fields": [
            ("qualifying_from", "Qualifying service from (blank = aided joining date)",
             "अर्हताकारी सेवा पासून (रिक्त = अनुदानित नियुक्ती)", "date", None),
            ("qualifying_to", "Qualifying service to (blank = retirement date)",
             "अर्हताकारी सेवा पर्यंत (रिक्त = सेवानिवृत्ती)", "date", None),
            ("unaided_from", "Un-aided service from", "विनाअनुदानित सेवा पासून", "date", None),
            ("unaided_to", "Un-aided service to", "विनाअनुदानित सेवा पर्यंत", "date", None),
            ("non_qualifying", "Non-qualifying service (Y/M/D)", "अनर्हताकारी सेवा (व/म/दि)",
             "duration", None),
            ("weightage", "Weightage (Y/M/D)", "वेटेज (व/म/दि)", "duration", None),
            ("military_service", "Military service", "सैन्य सेवा", "text", None),
            ("military_pension", "Military pension / gratuity", "सैन्य निवृत्तीवेतन", "text", None),
            ("foreign_service", "Foreign service", "परदेशी सेवा", "text", None),
            ("foreign_contribution", "Contributions received", "अंशदान प्राप्त", "text", None),
            ("dept_enquiry_pending", "Departmental enquiry pending", "विभागीय चौकशी प्रलंबित",
             "select", ["No", "Yes"]),
            ("dues_recoverable", "Dues recoverable", "वसुलीयोग्य रक्कम", "text", None),
            ("licence_fee", "Licence fee", "परवाना शुल्क", "text", None),
            ("withheld_pct", "Percentage withheld", "रोखलेली टक्केवारी", "text", None),
            ("gratuity_override", "Override gratuity amount (leave blank to compute)",
             "उपदान रक्कम बदला (रिक्त = आपोआप गणना)", "number", None),
        ],
    },
    {
        "key": "checklist",
        "title_en": "Head of office checklist",
        "title_mr": "मुख्याध्यापक तपासणी सूची",
        "fields": [
            ("allottee_govt_accommodation", "Allottee of government accommodation",
             "शासकीय निवासस्थान वाटप", "select", ["No", "Yes"]),
            ("date_service_assessed", "Date service assessed", "सेवा निश्चिती दिनांक", "date", None),
            ("date_dues_assessed", "Date dues assessed", "देणी निश्चिती दिनांक", "date", None),
            ("date_certificate_furnished", "Date certificate furnished",
             "प्रमाणपत्र दिल्याचा दिनांक", "date", None),
            ("objection_received", "Objection received", "आक्षेप प्राप्त", "select", ["No", "Yes"]),
            ("nomination_made", "Nomination made", "नामनिर्देशन केले", "select", ["Yes", "No"]),
            ("family_details_attached", "Family details attached", "कुटुंब तपशील जोडला",
             "select", ["Yes", "No"]),
            ("delay_reason_gr", "Reason for delay (GR reference)", "विलंबाचे कारण (शासन निर्णय)",
             "text", None),
            ("ag_receipt_date", "Date papers received by Accounts Officer",
             "लेखाधिकाऱ्यास कागदपत्रे मिळाल्याचा दिनांक", "date", None),
        ],
    },
]

# --------------------------------------------------------------------------
# Repeating tables
# --------------------------------------------------------------------------
TABLE_SECTIONS = [
    {
        "key": "service_history",
        "title_en": "History of service",
        "title_mr": "सेवा इतिहास",
        "help_en": "One row per pay change or posting. Durations are computed.",
        "help_mr": "प्रत्येक वेतनवाढ/नियुक्तीसाठी एक ओळ. कालावधी आपोआप मोजला जातो.",
        "columns": [
            ("establishment", "Establishment", "आस्थापना", "textarea"),
            ("appointment", "Appointment", "नियुक्ती", "text"),
            ("pay", "Pay", "वेतन", "text"),
            ("grade_pay", "Grade pay", "ग्रेड वेतन", "text"),
            ("frm", "From", "पासून", "date"),
            ("to", "To", "पर्यंत", "date"),
            ("remarks", "Remarks", "शेरा", "textarea"),
            ("verified", "How verified", "पडताळणी", "text"),
            ("audit_remarks", "Remarks by the Audit Office", "लेखा कार्यालयाचा शेरा", "text"),
        ],
        "computed": [("total", "Total period", "एकूण कालावधी", "duration", "frm", "to")],
        "total_row": ("total", "Total", "एकूण", "duration", "frm", "to"),
    },
    {
        "key": "school_service",
        "title_en": "Service certificate - schools",
        "title_mr": "सेवा प्रमाणपत्र - शाळा",
        "help_en": "Schools served, in order. Total service is computed per row.",
        "help_mr": "काम केलेल्या शाळा क्रमाने. एकूण सेवा आपोआप मोजली जाते.",
        "columns": [
            ("school", "Name of school", "शाळेचे नाव", "textarea"),
            ("designation", "Designation", "पदनाम", "text"),
            ("post_type", "Type of post", "पदाचा प्रकार", "text"),
            ("frm", "From", "पासून", "date"),
            ("to", "To", "पर्यंत", "date"),
            ("grant_status", "Grant status", "अनुदान स्थिती", "text"),
        ],
        "computed": [("total", "Total service", "एकूण सेवा", "duration", "frm", "to")],
        "total_row": ("total", "Total service", "एकूण सेवा", "duration", "frm", "to"),
    },
    {
        "key": "pay_sources",
        "title_en": "Sources of pay drawn",
        "title_mr": "वेतनाचे स्त्रोत",
        "help_en": "", "help_mr": "",
        "columns": [
            ("frm", "From", "पासून", "date"),
            ("to", "To", "पर्यंत", "date"),
            ("fund", "Paid from which fund", "कोणत्या निधीतून", "textarea"),
        ],
    },
    {
        "key": "leave",
        "title_en": "Leave availed",
        "title_mr": "उपभोगलेली रजा",
        "help_en": "Leave the days column blank to compute it from the dates.",
        "help_mr": "दिवस रिकामे ठेवल्यास दिनांकावरून आपोआप मोजले जातील.",
        "columns": [
            ("nature", "Nature of leave", "रजेचा प्रकार", "text"),
            ("frm", "From", "पासून", "date"),
            ("to", "To", "पर्यंत", "date"),
            ("days", "Number of days", "दिवस", "number"),
        ],
        "auto": [("days", "days", "frm", "to")],
        "total_row": ("days", "Total days", "एकूण दिवस", "days", "frm", "to"),
    },
    {
        "key": "family",
        "title_en": "Family members",
        "title_mr": "कुटुंब सदस्य",
        "help_en": "Leave age blank to compute it from the date of birth.",
        "help_mr": "वय रिकामे ठेवल्यास जन्मतारखेवरून मोजले जाईल.",
        "columns": [
            ("name", "Name", "नाव", "text"),
            ("dob", "Date of birth", "जन्मतारीख", "date"),
            ("age", "Age", "वय", "number"),
            ("relation", "Relationship", "नाते", "text"),
        ],
        "auto": [("age", "age", "dob", None)],
    },
    {
        "key": "nominees",
        "title_en": "Nomination for DCRG",
        "title_mr": "उपदान नामनिर्देशन",
        "help_en": "Alternate nominees are edited inside each nominee row.",
        "help_mr": "पर्यायी नामनिर्देशित व्यक्ती प्रत्येक ओळीत संपादित करा.",
        "columns": [
            ("name", "Nominee name", "नामनिर्देशिताचे नाव", "text"),
            ("address", "Address", "पत्ता", "textarea"),
            ("relation", "Relationship", "नाते", "text"),
            ("dob", "Date of birth", "जन्मतारीख", "date"),
            ("age", "Age", "वय", "number"),
            ("contingency", "Contingency invalidating nomination", "अवैध ठरण्याची स्थिती", "text"),
        ],
        "auto": [("age", "age", "dob", None)],
        "nested": {
            "key": "alternates",
            "title_en": "Alternate nominees",
            "title_mr": "पर्यायी नामनिर्देशित",
            "columns": [
                ("name", "Name", "नाव", "text"),
                ("relation", "Relationship", "नाते", "text"),
                ("dob", "Date of birth", "जन्मतारीख", "date"),
                ("age", "Age", "वय", "number"),
                ("share", "Share", "हिस्सा", "text"),
            ],
            "auto": [("age", "age", "dob", None)],
        },
    },
    {
        "key": "breaks",
        "title_en": "Breaks in service",
        "title_mr": "सेवाखंड",
        "help_en": "Leave empty when there is no break; the form then prints NIL.",
        "help_mr": "सेवाखंड नसल्यास रिकामे ठेवा; नमुन्यात 'NIL' छापले जाईल.",
        "columns": [
            ("institution", "Institution", "संस्था", "textarea"),
            ("reason", "Reason", "कारण", "text"),
            ("frm", "From", "पासून", "date"),
            ("to", "To", "पर्यंत", "date"),
            ("not_intervened", "Not intervened by other service", "इतर सेवेने खंडित नाही", "text"),
            ("followed_by", "Followed by school service", "पुढे शाळेत सेवा", "text"),
            ("condoned", "Condoned as per GR", "शासन निर्णयानुसार माफ", "text"),
            ("treated_as_duty", "Treated as duty (Y/M/D)", "कर्तव्य म्हणून गणले (व/म/दि)", "text"),
            ("remarks", "Remarks", "शेरा", "text"),
        ],
        "computed": [("total", "Total period", "एकूण कालावधी", "duration", "frm", "to")],
    },
]


# Fields that hold the same value in the other script. The Marathi side is the
# source: Devanagari records the pronunciation, so converting it to Latin is
# dependable, while the reverse has to guess vowel length and retroflexion.
SCRIPT_PAIRS = {'school': [('society_line_mr', 'society_line_en'), ('name_mr', 'name_en'), ('taluka_mr', 'taluka_en'), ('district_mr', 'district_en')],
    'meta': [('place_mr', 'place')],
    'office': [('addressee_mr', 'addressee_en'), ('eo_designation_mr', 'eo_designation_en')],
    'employee': [('name_mr', 'name_en'), ('father_name_mr', 'father_name_en'), ('spouse_name_mr', 'spouse_name_en'), ('designation_mr', 'designation_en'), ('addr_at_mr', 'addr_at'), ('addr_post_mr', 'addr_post'), ('addr_taluka_mr', 'addr_taluka'), ('addr_district_mr', 'addr_district')]}


def _fields(entries, section_key=""):
    pairs = dict(SCRIPT_PAIRS.get(section_key, []))
    reverse = {v: k for k, v in pairs.items()}
    out = []
    for k, en, mr, ftype, opts in entries:
        field = {"key": k, "label_en": en, "label_mr": mr, "type": ftype,
                 "options": opts}
        if k in pairs:
            field["pair"] = {"other": pairs[k], "direction": "mr2en"}
        elif k in reverse:
            field["pair"] = {"other": reverse[k], "direction": "en2mr"}
        out.append(field)
    return _marathi_first(out, pairs, reverse)


def _marathi_first(out, pairs, reverse):
    """Put the two halves of every paired field together, Marathi then English.

    The Marathi is the side to fill in -- it is what the forms are written in and
    the only direction that converts dependably -- so it reads first, with its
    English counterpart beside it. The pair sits where the earlier of the two was
    written, which leaves the rest of the section in the order it was declared.

    Doing it here rather than by hand in the lists above means a field added
    later cannot reintroduce the wrong order.
    """
    by_key = {f["key"]: f for f in out}

    # Fields written in both scripts but not declared convertible -- a department
    # name, say -- are read the same way round, so they are grouped too. Only
    # their order changes: no pair is recorded, so no conversion button appears.
    together = dict(pairs)
    for key in by_key:
        if not key.endswith("_mr") or key in pairs or key in reverse:
            continue
        for other in (key[:-3] + "_en", key[:-3]):
            if other in by_key and other not in pairs and other not in reverse:
                together[key] = other
                break
    partner = {v: k for k, v in together.items()}

    ordered, placed = [], set()
    for field in out:
        key = field["key"]
        if key in placed:
            continue
        mr_key = key if key in together else partner.get(key)
        en_key = together.get(mr_key) if mr_key else None
        if mr_key in by_key and en_key in by_key:
            for half in (mr_key, en_key):
                ordered.append(by_key[half])
                placed.add(half)
        else:
            ordered.append(field)
            placed.add(key)
    return ordered


# Columns that are usually left empty. They stay available behind a toggle so
# the grid shows only what a case normally needs.
OPTIONAL_COLUMNS = {'service_history': {'grade_pay', 'audit_remarks', 'verified'}, 'school_service': {'post_type'}, 'nominees': {'contingency'}, 'breaks': {'not_intervened', 'condoned', 'remarks', 'followed_by', 'treated_as_duty'}}


def _columns(entries, table_key=""):
    optional = OPTIONAL_COLUMNS.get(table_key, set())
    return [{"key": k, "label_en": en, "label_mr": mr, "type": ftype,
             "optional": k in optional}
            for k, en, mr, ftype in entries]


def _computed(entries):
    """Read-only columns the UI derives from other cells."""
    return [{"key": k, "label_en": en, "label_mr": mr, "kind": kind,
             "from": src, "to": dst}
            for k, en, mr, kind, src, dst in entries or []]


def _auto(entries):
    """Editable columns that fill themselves in when left blank."""
    return [{"target": target, "kind": kind, "from": src, "to": dst}
            for target, kind, src, dst in entries or []]


def _total_row(entry):
    if not entry:
        return None
    key, en, mr, kind, src, dst = entry
    return {"target": key, "label_en": en, "label_mr": mr, "kind": kind,
            "from": src, "to": dst}


def form_schema() -> dict:
    """The intake schema the React app renders."""
    return {
        "sections": [
            {**{k: v for k, v in section.items() if k != "fields"},
             "fields": _fields(section["fields"], section["key"])}
            for section in FIELD_SECTIONS
        ],
        "tables": [
            {**{k: v for k, v in table.items()
                if k not in ("columns", "nested", "computed", "auto", "total_row")},
             "columns": _columns(table["columns"], table["key"]),
             "computed": _computed(table.get("computed")),
             "auto": _auto(table.get("auto")),
             "total_row": _total_row(table.get("total_row")),
             "nested": ({**{k: v for k, v in table["nested"].items()
                            if k not in ("columns", "auto")},
                         "columns": _columns(table["nested"]["columns"]),
                         "auto": _auto(table["nested"].get("auto"))}
                        if table.get("nested") else None)}
            for table in TABLE_SECTIONS
        ],
        "refs": {
            "title_en": "Government resolution references (covering letter)",
            "title_mr": "शासन निर्णय संदर्भ (सोबतचे पत्र)",
        },
    }
