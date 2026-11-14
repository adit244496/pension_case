# -*- coding: utf-8 -*-
"""Create the schema, register the form templates, and load a sample case.

Re-running this is safe: templates and text blocks are upserted by key, and
an admin's edited block text is preserved (only ``default_value`` is refreshed).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session

from build_templates import docx_name_for                     # noqa: E402
from forms import ALL_FORMS                                   # noqa: E402

from .auth import ensure_default_user                          # noqa: E402
from .db import SessionLocal                                   # noqa: E402
from .migrate import migrate                                   # noqa: E402
from .models import Case, FormTemplate, TextBlock             # noqa: E402


def sync_templates(db: Session, *, reset_text: bool = False) -> int:
    """Register every form defined in code, keeping admin edits intact."""
    count = 0
    for meta in ALL_FORMS:
        tpl = db.query(FormTemplate).filter_by(code=meta["code"]).one_or_none()
        if tpl is None:
            tpl = FormTemplate(code=meta["code"], enabled=meta.get("enabled", True),
                               builtin=True)
            db.add(tpl)
        elif tpl.archived:
            continue          # the admin removed this form; do not bring it back
        tpl.builtin = True
        tpl.order_no = meta["order"]
        tpl.title_en = meta["title_en"]
        tpl.title_mr = meta["title_mr"]
        tpl.language = meta.get("language", "en")
        tpl.landscape = meta.get("landscape", False)
        if not tpl.docx_name:
            tpl.docx_name = docx_name_for(meta["code"])
        db.flush()

        existing = {b.key: b for b in tpl.blocks}
        for order, (key, label, default, multiline) in enumerate(meta.get("blocks", [])):
            block = existing.get(key)
            if block is None:
                block = TextBlock(template_id=tpl.id, key=key, value=default)
                db.add(block)
            block.label = label
            block.default_value = default
            block.order_no = order
            block.multiline = multiline
            if reset_text:
                block.value = default
        count += 1
    db.commit()
    return count


# --------------------------------------------------------------------------
# Sample case -- the reference file this system was modelled on.
# --------------------------------------------------------------------------
SAMPLE_CASE = {
    "meta": {
        "case_no": "DCRG-2026-001",
        "letter_ref_no": "2026-27/",
        "letter_date": "28-08-2026",
        "place": "Loni Bk.",
        "place_mr": "लोणी बुद्रूक",
        "application_date": "27-08-2026",
        "class_of_pension": "Superannuation",
    },
    "school": {
        "society_line_mr": "लोकनेते डॉ.बाळासाहेब विखे पाटील (पदमभूषण उपाधीने सन्मानित) "
                           "प्रवरा ग्रामीण शिक्षण संस्थेचे",
        "society_line_en": "Loknete Dr.Balasaheb Vikhe Patil (Padma Bhushan Awardee) "
                           "Pravara Rural Education Society, Pravaranagar",
        "name_mr": "पुण्यश्लोक अहिल्याबाई होळकर माध्यमिक विद्यालय, लोणी बुद्रूक",
        "name_en": "PUNYASHLOK AHILYABAI HOLKAR MADHYAMIC VIDYALAYA, LONI BK.",
        "taluka_mr": "राहाता", "taluka_en": "RAHATA",
        "district_mr": "अहिल्यानगर", "district_en": "AHILYANAGAR",
        "pin": "413 736",
        "hm_name_mr": "", "hm_name_en": "",
        "ddo_code": "5401001878",
        "department_en": "Secondary Education",
        "department_mr": "माध्यमिक शिक्षण",
    },
    "office": {
        "addressee_mr": "मा.शिक्षणाधिकारी (माध्य.),\nवेतन व भविष्य निर्वाह निधी पथक,\nअहिल्यानगर.",
        "addressee_en": "Education Officer (Secondary),\nPay & Provident Fund Unit, Ahilyanagar",
        "eo_designation_mr": "शिक्षणाधिकारी (माध्य.) जि.प. अहिल्यानगर",
        "eo_designation_en": "The Education officer (Sec.) Z. P. Ahilyanagar",
        "zp_district_mr": "अहिल्यानगर", "zp_district_en": "Ahilyanagar",
        "treasury": "AHILYANAGAR DIST. TREASURY",
        "to_pension": "Ahilyanagar", "to_dcrg": "Ahilyanagar",
        "ag_office_en": "The Account General,\nMaharashtra State, Mumbai",
    },
    "employee": {
        "name_mr": "श्री.अण्णासाहेब रंगनाथ कडलग",
        "name_en": "Shri.Annasaheb Rangnath Kadlag",
        "father_name_mr": "श्री.रंगनाथ गणपत कडलग",
        "father_name_en": "SHRI.RANGNATH GANPAT KADLAG",
        "mother_name_en": "SMT.CHANGUNABAI RANGNATH KADLAG",
        "spouse_name_en": "Mrs.Indubai Rangnath Kadlag",
        "spouse_name_mr": "श्रीमती इंदुबाई रंगनाथ कडलग",
        "designation_mr": "शिपाई",
        "designation_en": "Full Time Peon",
        "group_class": "IV", "sex": "Male",
        "religion_caste": "HINDU-MARATHA (OPEN)", "nationality": "INDIAN",
        "dob": "03-03-1964",
        "doj_unaided": "01-09-2005",
        "doj_aided": "01-03-2008",
        "dor": "31-03-2024",
        "mobile": "9850042258", "email": "",
        "aadhaar": "3726 0499 6966", "pan": "BCCPK8886M",
        "addr_at": "SADATPUR", "addr_post": "GOGALGAON",
        "addr_taluka": "SANGAMNER", "addr_district": "AHILYANAGAR",
        "addr_pin": "413 736", "addr_state": "MAHARASHTRA",
        "addr_at_mr": "सादतपूर", "addr_post_mr": "गोगलगांव",
        "addr_taluka_mr": "संगमनेर", "addr_district_mr": "अहिल्यानगर",
        "height": "5'.3\"",
        "identification_marks": ["Healed mark over left side neck.", "A mole over left leg."],
        "substantive": "Substantive",
    },
    "pay": {
        "level": "LVL S-3", "matrix": "PAY MATRIX -16600-52400",
        "basic": "28200", "grade_pay": "",
        "da_pct": "50", "da_amt": "14100",
        "hra_pct": "9", "hra_amt": "2538",
        "travel_allowance": "675",
        "other_allowance": "", "income_tax": "",
        "total_salary": "45513",
        "last_pay_for_gratuity": "28200",
        "paid_upto": "March- 2024",
        "average_emoluments": "28200", "npa": "",
    },
    "bank": {
        "name": "Bank Of Maharashtra, Babhaleshwar.",
        "branch": "Babhaleshwar",
        "branch_address": "Loni Road, Opp.Ghogare Petrol Pump,\n"
                          "At/Post-Babhaleshwar. Tal.Rahata,\nDist.Ahilyanagar. Pin-413 713",
        "account_no": "60121049339",
        "micr": "413014503", "ifsc": "MAHB0001608",
        "gpf_no": "ANG- 22582",
    },
    "service": {
        "qualifying_from": "", "qualifying_to": "",
        "unaided_from": "01-09-2005", "unaided_to": "29-02-2008",
        "non_qualifying": {"y": 0, "m": 0, "d": 0},
        "weightage": {"y": 0, "m": 0, "d": 0},
        "military_service": "Nil", "military_pension": "Nil",
        "foreign_service": "Nil", "foreign_contribution": "Nil",
        "dept_enquiry_pending": "No",
        "dues_recoverable": "NIL", "licence_fee": "NA",
        "withheld_pct": "00%", "gratuity_override": "",
    },
    "tables": {
        "service_history": [
            {"establishment": "Loknete Dr.Balasaheb Vikhe Patil (Padmabhushan Awardee) "
                              "PRES'S Yogiraj Changdev Maharaj Vidyalaya, Puntamba. "
                              "Tal.Rahata, Dist.Ahilyanagar.",
             "appointment": "Full Time Peon.", "pay": "2550/-", "grade_pay": "",
             "frm": "01-09-2005", "to": "31-12-2005",
             "remarks": "Appointed as a full time Peon in the Pay Scale of "
                        "Rs.2550-55-2660-60-3200 w.e.f.01-09-2005 on un aided basis & "
                        "joined his duties on same date b.o.h. For 6th Pay Scale fixation",
             "verified": ""},
            {"establishment": "\"", "appointment": "Pay Band Grade Pay",
             "pay": "4750/-", "grade_pay": "1300/-",
             "frm": "01-01-2006", "to": "30-06-2006", "remarks": "", "verified": ""},
            {"establishment": "\"", "appointment": "Pay Band Grade Pay",
             "pay": "4940/-", "grade_pay": "1300/-",
             "frm": "01-07-2006", "to": "31-08-2006", "remarks": "", "verified": ""},
            {"establishment": "\"", "appointment": "Pay Band Grade Pay",
             "pay": "4940/-", "grade_pay": "1300/-",
             "frm": "01-09-2006", "to": "28-02-2007",
             "remarks": "60% aided w.e.f. 01-09-2006", "verified": ""},
            {"establishment": "\"", "appointment": "Pay Band Grade Pay",
             "pay": "4940/-", "grade_pay": "1300/-",
             "frm": "01-03-2007", "to": "30-06-2007",
             "remarks": "80% aided w.e.f.01-03-2007", "verified": ""},
            {"establishment": "\"", "appointment": "Pay Band Grade Pay",
             "pay": "5130/-", "grade_pay": "1300/-",
             "frm": "01-07-2007", "to": "29-02-2008",
             "remarks": "80% aided", "verified": ""},
            {"establishment": "\"", "appointment": "Pay Band Grade Pay",
             "pay": "5130/-", "grade_pay": "1300/-",
             "frm": "01-03-2008", "to": "30-06-2008",
             "remarks": "100% aided w.e.f.01-03-2008", "verified": ""},
            {"establishment": "\"", "appointment": "Pay Band Grade Pay",
             "pay": "5330/-", "grade_pay": "1300/-",
             "frm": "01-07-2008", "to": "30-06-2009", "remarks": "", "verified": ""},
            {"establishment": "\"", "appointment": "Pay Band Grade Pay",
             "pay": "5530/-", "grade_pay": "1300/-",
             "frm": "01-07-2009", "to": "30-06-2010", "remarks": "", "verified": ""},
            {"establishment": "\"", "appointment": "Pay Band Grade Pay",
             "pay": "5740/-", "grade_pay": "1300/-",
             "frm": "01-07-2010", "to": "30-06-2011", "remarks": "", "verified": ""},
            {"establishment": "\"", "appointment": "Pay Band Grade Pay",
             "pay": "5960/-", "grade_pay": "1300/-",
             "frm": "01-07-2011", "to": "30-06-2012", "remarks": "", "verified": ""},
            {"establishment": "\"", "appointment": "Pay Band Grade Pay",
             "pay": "6180/-", "grade_pay": "1300/-",
             "frm": "01-07-2012", "to": "30-06-2013", "remarks": "", "verified": ""},
            {"establishment": "\"", "appointment": "Pay Band Grade Pay",
             "pay": "6410/-", "grade_pay": "1300/-",
             "frm": "01-07-2013", "to": "30-06-2014", "remarks": "", "verified": ""},
            {"establishment": "\"", "appointment": "Pay Band Grade Pay",
             "pay": "6650/-", "grade_pay": "1300/-",
             "frm": "01-07-2014", "to": "31-10-2014",
             "remarks": "Transferred", "verified": ""},
            {"establishment": "Shri.Yashwantrao Chavan Vidyalaya, Rajuri. Tal.Rahata, "
                              "Dist.Ahilyanagar",
             "appointment": "F. T.Peon Pay Band Grade Pay",
             "pay": "6650/-", "grade_pay": "1300/-",
             "frm": "01-11-2014", "to": "30-06-2015", "remarks": "", "verified": ""},
            {"establishment": "\"", "appointment": "Pay Band Grade Pay",
             "pay": "6890/-", "grade_pay": "1300/-",
             "frm": "01-07-2015", "to": "31-12-2015",
             "remarks": "For 7th Pay Scale fixation", "verified": ""},
            {"establishment": "@ In the Pay Level S-1 Pay Matrix 15000-47600.",
             "appointment": "\"", "pay": "22100/-", "grade_pay": "",
             "frm": "01-01-2016", "to": "30-06-2016", "remarks": "", "verified": ""},
            {"establishment": "\"", "appointment": "\"", "pay": "22800/-", "grade_pay": "",
             "frm": "01-07-2016", "to": "30-06-2017", "remarks": "", "verified": ""},
            {"establishment": "\"", "appointment": "\"", "pay": "23600/-", "grade_pay": "",
             "frm": "01-07-2017", "to": "31-08-2017",
             "remarks": "For Time bound Promotion Scale (Sr.Scale)", "verified": ""},
            {"establishment": "@ In the Pay Level S-3 Pay Matrix 16600-52400.",
             "appointment": "\"", "pay": "24300/-", "grade_pay": "",
             "frm": "01-09-2017", "to": "30-06-2018", "remarks": "", "verified": ""},
            {"establishment": "\"", "appointment": "\"", "pay": "25000/-", "grade_pay": "",
             "frm": "01-07-2018", "to": "30-06-2019", "remarks": "", "verified": ""},
            {"establishment": "\"", "appointment": "\"", "pay": "25800/-", "grade_pay": "",
             "frm": "01-07-2019", "to": "30-06-2020", "remarks": "", "verified": ""},
            {"establishment": "\"", "appointment": "\"", "pay": "26600/-", "grade_pay": "",
             "frm": "01-07-2020", "to": "31-08-2021",
             "remarks": "Transferred", "verified": ""},
            {"establishment": "Punyashlok Ahilyabai Holkar Mdhyamic Vidyalaya, Loni Bk. "
                              "Tal.Rahata, Dist.Ahilyanagar",
             "appointment": "Full Time Peon", "pay": "26600/-", "grade_pay": "",
             "frm": "01-09-2021", "to": "30-06-2022", "remarks": "", "verified": ""},
            {"establishment": "\"", "appointment": "\"", "pay": "27400/-", "grade_pay": "",
             "frm": "01-07-2022", "to": "30-06-2023", "remarks": "", "verified": ""},
            {"establishment": "\"", "appointment": "\"", "pay": "28200/-", "grade_pay": "",
             "frm": "01-07-2023", "to": "31-03-2024",
             "remarks": "Retired on Superannuation.", "verified": ""},
        ],
        "school_service": [
            {"school": "Yogiraj Changdev Maharaj Vidyalaya, Puntamba Tal.Rahata, "
                       "Dist.Ahilyanagar.",
             "designation": "Full Time Peon", "post_type": "Full Time",
             "frm": "01-09-2005", "to": "31-08-2006", "grant_status": "un-aided"},
            {"school": "", "designation": "\"", "post_type": "Full Time",
             "frm": "01-09-2006", "to": "28-02-2007", "grant_status": "60% aided"},
            {"school": "", "designation": "\"", "post_type": "Full Time",
             "frm": "01-03-2007", "to": "29-02-2008", "grant_status": "80% aided"},
            {"school": "", "designation": "\"", "post_type": "Full Time",
             "frm": "01-03-2008", "to": "31-10-2014", "grant_status": "100% aided"},
            {"school": "Shri Yashwantrao Chavan Vidyalaya, Rajuri. Tal.Rahata, "
                       "Dist.Ahilyanagar",
             "designation": "Full Time Peon", "post_type": "Full Time",
             "frm": "01-11-2014", "to": "31-08-2021", "grant_status": "100% aided"},
            {"school": "Punyashlok Ahilyabai Holkar Madhyamic Vidyalaya, Loni Bk. "
                       "Tal.Rahata, Dist.Ahilyanagar",
             "designation": "\"", "post_type": "Full Time",
             "frm": "01-09-2021", "to": "31-03-2024", "grant_status": "100% aided"},
        ],
        "pay_sources": [
            {"frm": "01-09-2005", "to": "31-08-2006", "fund": "100%  Sanstha Salary Fund"},
            {"frm": "01-09-2006", "to": "28-02-2007",
             "fund": "40%  Sanstha Salary Fund\n&\n60%  Salary Grant from Education "
                     "Department of M.S.(60% aided)"},
            {"frm": "01-03-2007", "to": "29-02-2008",
             "fund": "20%  Sanstha Salary Fund\n&\n80%  Salary Grant from Education "
                     "Department of M.S.(80% aided)"},
            {"frm": "01-03-2008", "to": "31-03-2024",
             "fund": "100% Salary Grant from  Education Department of Maharashtra State"},
        ],
        "leave": [
            {"nature": "Earned Leave credited", "frm": "22-11-2011", "to": "26-11-2011", "days": "5"},
            {"nature": "\"", "frm": "16-01-2012", "to": "29-01-2012", "days": "14"},
            {"nature": "\"", "frm": "14-04-2012", "to": "25-04-2012", "days": "12"},
            {"nature": "\"", "frm": "29-07-2013", "to": "04-08-2013", "days": "7"},
            {"nature": "\"", "frm": "19-11-2013", "to": "01-12-2013", "days": "13"},
            {"nature": "\"", "frm": "26-09-2017", "to": "14-10-2017", "days": "19"},
            {"nature": "\"", "frm": "18-12-2017", "to": "12-01-2018", "days": "26"},
            {"nature": "\"", "frm": "09-01-2019", "to": "18-01-2019", "days": "10"},
            {"nature": "\"", "frm": "12-04-2021", "to": "10-05-2021", "days": "29"},
            {"nature": "\"", "frm": "01-02-2022", "to": "11-02-2022", "days": "11"},
            {"nature": "\"", "frm": "08-03-2022", "to": "17-04-2022", "days": "31"},
            {"nature": "\"", "frm": "08-05-2023", "to": "16-05-2023", "days": "9"},
            {"nature": "\"", "frm": "10-10-2023", "to": "19-10-2023", "days": "10"},
        ],
        "family": [
            {"name": "Mrs.Indubai Rangnath Kadlag", "dob": "03-06-1967", "relation": "Wife",
             "age": "60"},
            {"name": "Mr. Eknath Annasaheb Kadlag", "dob": "16-07-1987",
             "relation": "Major Son", "age": "40"},
            {"name": "Mr. Sunil Annasaheb Kadlag", "dob": "06-04-1989",
             "relation": "Major Son", "age": "38"},
            {"name": "Mr. Anil Annasaheb Kadlag", "dob": "19-03-1991",
             "relation": "Major Son", "age": "36"},
        ],
        "nominees": [
            {"name": "Mrs. Indubai Annasaheb Kadlag",
             "address": "At-Sadatpur\nPost-Gogalgaon\nTal.-Sangamner,\n"
                        "Dist – Ahilyanagar.\nPin-  413 736",
             "relation": "wife", "age": "60", "contingency": "Death/ Insanity",
             "alternates": [
                 {"name": "Mr.Eknath Annasaheb Kadlag", "relation": "Son",
                  "dob": "16-07-1987", "age": "40", "share": "35%"},
                 {"name": "Mr.Sunil Annasaheb Kadlag", "relation": "Son",
                  "dob": "06-04-1989", "age": "38", "share": "35%"},
                 {"name": "Mr.Anil Annasaheb Kadlag", "relation": "Son",
                  "dob": "19-03-1991", "age": "36", "share": "30%"},
             ]},
        ],
        "breaks": [],
    },
    "refs": [
        "वित्त विभाग शासन निर्णय क्र.रानियो-2022/प्र.क्र.34/सेवा-4 दि.31.03.2023",
        "शासन शुद्धीपत्रक क्र.रानियो-2022/प्र.क्र.34/सेवा-4 दिनांक 20.04.2023",
        "शालेय शिक्षण व क्रीडा विभाग, महाराष्ट्र शासन निर्णय क्रमांक अनियो-2023/"
        "प्र.क्र.28/टीएनटी-6 दिनांक 14 जून, 2023",
        "वित्त विभाग शासन परिपत्रक क्र.सेनिप्र.- 2023/प्र.क्र.57/सेवा-4 दि.24.08.2024",
    ],
    "checklist": {
        "allottee_govt_accommodation": "No",
        "date_service_assessed": "27-08-2026",
        "date_dues_assessed": "28-08-2026",
        "date_certificate_furnished": "28-08-2026",
        "objection_received": "No",
        "nomination_made": "Yes",
        "family_details_attached": "Yes",
        "delay_reason_gr": "As per G.R.Dated 24th August, 2023",
        "ag_receipt_date": "28-08-2026",
    },
}


def seed_sample_case(db: Session) -> Case:
    case = db.query(Case).filter_by(case_no=SAMPLE_CASE["meta"]["case_no"]).one_or_none()
    if case is None:
        case = Case(case_no=SAMPLE_CASE["meta"]["case_no"])
        db.add(case)
    case.data = SAMPLE_CASE
    case.employee_name_en = SAMPLE_CASE["employee"]["name_en"]
    case.employee_name_mr = SAMPLE_CASE["employee"]["name_mr"]
    case.status = "ready"
    db.commit()
    db.refresh(case)
    return case


def main(with_sample: bool = True, reset_text: bool = False):
    changes = migrate()
    if changes:
        print("Schema updated:", ", ".join(changes))
    db = SessionLocal()
    try:
        n = sync_templates(db, reset_text=reset_text)
        print(f"Registered {n} form templates.")
        created = ensure_default_user(db)
        if created:
            from .auth import DEFAULT_PASSWORD, DEFAULT_USERNAME
            print(f"Default login created: {DEFAULT_USERNAME} / {DEFAULT_PASSWORD}")
        if with_sample:
            case = seed_sample_case(db)
            print(f"Sample case ready: {case.case_no} ({case.employee_name_en})")
    finally:
        db.close()


if __name__ == "__main__":
    main(with_sample="--no-sample" not in sys.argv,
         reset_text="--reset-text" in sys.argv)
