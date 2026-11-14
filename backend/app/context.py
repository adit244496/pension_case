"""Turns a stored case (plain JSON) into the context the .docx templates render.

Templates never do arithmetic.  Everything a form needs -- durations, the
six-monthly period count, the DCRG amount, per-row ages and totals -- is
derived here once and exposed under a small set of names:

    school, emp, pay, bank, office, svc, tbl, refs, chk, t, doc

``t`` holds the admin-editable text blocks of the template being rendered.
"""
from __future__ import annotations

import copy
from datetime import date
from typing import Any

from . import compute as C

# --------------------------------------------------------------------------
# The canonical shape of a case.  Also drives the intake screens in the UI.
# --------------------------------------------------------------------------
EMPTY_CASE: dict[str, Any] = {
    "meta": {
        "case_no": "",
        "letter_ref_no": "",
        "letter_date": "",
        "place": "",
        "place_mr": "",
        "application_date": "",
        "class_of_pension": "Superannuation",
        "class_of_pension_mr": "नियत वयोमानानुसार सेवानिवृत्ती",
        # While on, the GR references follow the system defaults.
        "refs_auto": True,
    },
    "school": {
        "society_line_mr": "",
        "society_line_en": "",
        "name_mr": "",
        "name_en": "",
        "taluka_mr": "", "taluka_en": "",
        "district_mr": "", "district_en": "",
        "pin": "",
        "hm_name_mr": "", "hm_name_en": "",
        "ddo_code": "",
        "department_en": "Secondary Education",
        "department_mr": "माध्यमिक शिक्षण",
    },
    "office": {
        "addressee_mr": "", "addressee_en": "",
        "eo_designation_mr": "", "eo_designation_en": "",
        "zp_district_mr": "", "zp_district_en": "",
        "treasury": "",
        "to_pension": "", "to_dcrg": "",
        "ag_office_en": "The Account General,\nMaharashtra State, Mumbai",
    },
    "employee": {
        "name_mr": "", "name_en": "",
        "father_name_mr": "", "father_name_en": "",
        "mother_name_en": "",
        "spouse_name_en": "", "spouse_name_mr": "",
        "designation_mr": "", "designation_en": "",
        "group_class": "", "sex": "Male",
        "religion_caste": "", "nationality": "INDIAN",
        "dob": "",
        "doj_unaided": "", "doj_aided": "",
        "dor": "",
        "mobile": "", "email": "",
        "aadhaar": "", "pan": "",
        "addr_at": "", "addr_post": "", "addr_taluka": "",
        "addr_district": "", "addr_pin": "", "addr_state": "MAHARASHTRA",
        # Marathi spellings, used by the Marathi letters and certificates
        "addr_at_mr": "", "addr_post_mr": "", "addr_taluka_mr": "",
        "addr_district_mr": "",
        "height": "",
        "identification_marks": [],
        "substantive": "Substantive",
        # Uploaded image, pasted into the photographs sheet. Stored as a file
        # name under the case's photos/ directory.
        "photo": "",
    },
    "pay": {
        "level": "", "matrix": "",
        "basic": "", "grade_pay": "",
        "da_pct": "", "da_amt": "",
        "hra_pct": "", "hra_amt": "",
        "travel_allowance": "",
        "other_allowance": "",
        "income_tax": "",
        "total_salary": "",
        "last_pay_for_gratuity": "",
        "paid_upto": "",
        "average_emoluments": "",
        "npa": "",
    },
    "bank": {
        "name": "", "branch": "", "branch_address": "",
        "account_no": "", "micr": "", "ifsc": "",
        "gpf_no": "",
    },
    "service": {
        "qualifying_from": "",            # blank -> employee.doj_aided
        "qualifying_to": "",              # blank -> employee.dor
        "unaided_from": "", "unaided_to": "",
        "non_qualifying": {"y": 0, "m": 0, "d": 0},
        "weightage": {"y": 0, "m": 0, "d": 0},
        "military_service": "Nil",
        "military_pension": "Nil",
        "foreign_service": "Nil",
        "foreign_contribution": "Nil",
        "dept_enquiry_pending": "No",
        "dues_recoverable": "NIL",
        "licence_fee": "NA",
        "withheld_pct": "00%",
        "gratuity_override": "",          # set only to override the computed DCRG
    },
    "tables": {
        "service_history": [],   # establishment, appointment, pay, grade_pay, frm, to, remarks
        "school_service": [],    # school, designation, frm, to, grant_status
        "pay_sources": [],       # frm, to, fund
        "leave": [],             # nature, frm, to, days
        "family": [],            # name, dob, relation
        "nominees": [],          # name, address, relation, age, contingency, alternates[]
        "breaks": [],            # institution, reason, frm, to, remarks
    },
    # Per-case form preferences: {code: {"order": int, "included": bool}}.
    # Kept on the case rather than on the generated rows, which are replaced
    # every time the documents are rebuilt.
    "forms": {},
    "refs": [],                  # GR references quoted in the covering letter
    "checklist": {
        "allottee_govt_accommodation": "No",
        "date_service_assessed": "",
        "date_dues_assessed": "",
        "date_certificate_furnished": "",
        "objection_received": "No",
        "nomination_made": "Yes",
        "family_details_attached": "Yes",
        "delay_reason_gr": "",
        "ag_receipt_date": "",
    },
}


def merge_defaults(data: dict | None) -> dict:
    """Overlay a stored case onto EMPTY_CASE so missing keys never break a form."""
    out = copy.deepcopy(EMPTY_CASE)
    if not data:
        return out
    for section, value in data.items():
        if isinstance(value, dict) and isinstance(out.get(section), dict):
            out[section] = {**out[section], **value}
        else:
            out[section] = value
    return out


# --------------------------------------------------------------------------
# derived values
# --------------------------------------------------------------------------
def _dur(payload) -> C.Duration:
    if isinstance(payload, C.Duration):
        return payload
    payload = payload or {}
    return C.Duration(payload.get("y") or 0, payload.get("m") or 0, payload.get("d") or 0)


def _num(value, default=0):
    try:
        return float(str(value).replace(",", "").replace("/-", "").strip())
    except (TypeError, ValueError):
        return default


def build_service(case: dict) -> dict:
    """Qualifying service, six-monthly periods and the gratuity amount."""
    emp, svc = case["employee"], case["service"]

    q_from = svc.get("qualifying_from") or emp.get("doj_aided") or emp.get("doj_unaided")
    q_to = svc.get("qualifying_to") or emp.get("dor")

    gross = C.duration_between(q_from, q_to)
    non_qualifying = _dur(svc.get("non_qualifying"))
    weightage = _dur(svc.get("weightage"))
    net = (gross - non_qualifying) + weightage

    unaided = C.duration_between(
        svc.get("unaided_from") or emp.get("doj_unaided"),
        svc.get("unaided_to") or _day_before(emp.get("doj_aided")),
    )

    # Total rendered service across every school listed on the service certificate.
    rendered_rows = [C.duration_between(r.get("frm"), r.get("to"))
                     for r in case["tables"].get("school_service", [])]
    rendered = C.sum_durations(rendered_rows) if rendered_rows else (unaided + gross)

    periods = C.six_monthly_periods(net)
    last_pay = _num(case["pay"].get("last_pay_for_gratuity") or case["pay"].get("basic"))

    override = svc.get("gratuity_override")
    amount = int(_num(override)) if str(override).strip() else \
        C.retirement_gratuity(last_pay, periods)

    unaided_end = svc.get("unaided_to") or _day_before(emp.get("doj_aided"))

    return {
        "qualifying_from": q_from,
        "qualifying_to": q_to,
        "unaided_end_f": C.fmt_date(unaided_end),
        "qualifying_from_f": C.fmt_date(q_from),
        "qualifying_to_f": C.fmt_date(q_to),
        "gross": gross.as_dict(),
        "non_qualifying": non_qualifying.as_dict(),
        "weightage": weightage.as_dict(),
        "net": net.as_dict(),
        "unaided": unaided.as_dict(),
        "rendered": rendered.as_dict(),
        "periods": periods,
        "periods_words": f"{periods} Terms",
        "last_pay": last_pay,
        "last_pay_r": C.rupees(last_pay),
        "dcrg": amount,
        "dcrg_r": C.rupees(amount),
        "dcrg_words_en": C.amount_words_en(amount),
        "dcrg_words_mr": C.amount_words_mr(amount),
        "dcrg_formula": f"{int(last_pay)} x {periods}/4",
        "capped": periods >= C.DCRG_MAX_PERIODS,
    }


def _day_before(value):
    from datetime import timedelta
    d = C.parse_date(value)
    return (d - timedelta(days=1)) if d else None


DITTO = '"'


def _ditto(rows: list[dict], field: str) -> None:
    """Leave a repeated value blank on the intake screen, print a ditto mark.

    The printed forms repeat a long establishment name with a ditto rather than
    writing it out again, so the operator only fills the column in when it
    actually changes.
    """
    for index, row in enumerate(rows):
        if index and not str(row.get(field) or "").strip():
            row[field] = DITTO


def build_tables(case: dict, on_date) -> dict:
    """Copy the repeating tables, adding per-row computed columns."""
    src = case["tables"]

    service_history = []
    for row in src.get("service_history", []):
        row = dict(row)
        dur = C.duration_between(row.get("frm"), row.get("to"))
        duty = _dur(row.get("duty")) if row.get("duty") else dur
        row.update({
            "frm_f": C.fmt_date(row.get("frm")),
            "to_f": C.fmt_date(row.get("to")),
            "total": dur.dashed,
            "duty": duty.dashed,
            "total_d": dur.as_dict(),
        })
        service_history.append(row)
    _ditto(service_history, "establishment")
    _ditto(service_history, "appointment")

    school_service = []
    for row in src.get("school_service", []):
        row = dict(row)
        dur = C.duration_between(row.get("frm"), row.get("to"))
        row.update({"frm_f": C.fmt_date(row.get("frm")),
                    "to_f": C.fmt_date(row.get("to")),
                    "total": dur.dashed, "total_d": dur.as_dict()})
        school_service.append(row)
    # The service certificate leaves the school name blank on a continuation
    # row and dittos only the designation, as the printed original does.
    _ditto(school_service, "designation")

    pay_sources = [{**r,
                    "frm_f": C.fmt_date(r.get("frm")),
                    "to_f": C.fmt_date(r.get("to"))}
                   for r in src.get("pay_sources", [])]

    leave = []
    total_leave = 0
    for row in src.get("leave", []):
        row = dict(row)
        days = row.get("days")
        if not str(days or "").strip():
            a, b = C.parse_date(row.get("frm")), C.parse_date(row.get("to"))
            days = (b - a).days + 1 if a and b else ""
        row.update({"frm_f": C.fmt_date(row.get("frm")),
                    "to_f": C.fmt_date(row.get("to")),
                    "days": days,
                    "days_f": f"{int(days):02d} days" if str(days).strip().isdigit() else days})
        total_leave += int(days) if str(days).strip().isdigit() else 0
        leave.append(row)
    _ditto(leave, "nature")

    family = []
    for idx, row in enumerate(src.get("family", []), start=1):
        row = dict(row)
        row.update({"sr": idx,
                    "dob_f": C.fmt_date(row.get("dob")),
                    "age": row.get("age") or C.age_on(row.get("dob"), on_date)})
        family.append(row)

    nominees = []
    for row in src.get("nominees", []):
        row = dict(row)
        alternates = []
        for a_idx, alt in enumerate(row.get("alternates", []), start=1):
            alt = dict(alt)
            alt.update({"sr": a_idx,
                        "dob_f": C.fmt_date(alt.get("dob")),
                        "age": alt.get("age") or C.age_on(alt.get("dob"), on_date)})
            alternates.append(alt)
        row["alternates"] = alternates
        row["age"] = row.get("age") or C.age_on(row.get("dob"), on_date)
        row["dob_f"] = C.fmt_date(row.get("dob"))
        nominees.append(row)

    breaks = [{**r, "frm_f": C.fmt_date(r.get("frm")), "to_f": C.fmt_date(r.get("to"))}
              for r in src.get("breaks", [])]

    return {
        "service_history": service_history,
        "school_service": school_service,
        "pay_sources": pay_sources,
        "leave": leave,
        "leave_total": total_leave,
        "family": family,
        "nominees": nominees,
        "breaks": breaks,
    }


def build_employee(case: dict) -> dict:
    """Employee block with pre-formatted dates and assembled address lines."""
    emp = dict(case["employee"])
    emp.update({
        "dob_f": C.fmt_date(emp.get("dob")),
        "dob_dev": C.fmt_date_dev(emp.get("dob")),
        "dor_f": C.fmt_date(emp.get("dor")),
        "dor_dev": C.fmt_date_dev(emp.get("dor")),
        "doj_unaided_f": C.fmt_date(emp.get("doj_unaided")),
        "doj_aided_f": C.fmt_date(emp.get("doj_aided")),
        "age_at_retirement": C.age_on(emp.get("dob"), emp.get("dor")),
        "name_en_upper": (emp.get("name_en") or "").upper(),
        "designation_en_upper": (emp.get("designation_en") or "").upper(),
    })
    # "01-09-2005 (UN AIDED), 01-03-2008 (100% AIDED)" -- appears on many forms.
    joined = []
    if emp.get("doj_unaided"):
        joined.append(f"{emp['doj_unaided_f']} (UN AIDED)")
    if emp.get("doj_aided"):
        joined.append(f"{emp['doj_aided_f']} (100% AIDED)")
    emp["doj_combined"] = ", ".join(joined)

    address_lines = []
    if emp.get("addr_at") or emp.get("addr_post"):
        address_lines.append(f"At.- {emp.get('addr_at', '')}, Post-{emp.get('addr_post', '')}.")
    if emp.get("addr_taluka"):
        address_lines.append(f"Tal.- {emp['addr_taluka']},")
    if emp.get("addr_district"):
        address_lines.append(f"Dist.- {emp['addr_district']} Pin- {emp.get('addr_pin', '')}")
    emp["address_block"] = "\n".join(address_lines)
    emp["address_inline"] = " ".join(address_lines)
    for field in ("at", "post", "taluka", "district"):
        emp[f"addr_{field}_mr"] = emp.get(f"addr_{field}_mr") or emp.get(f"addr_{field}", "")
    emp["marks_list"] = emp.get("identification_marks") or []
    return emp


def build_pay(case: dict) -> dict:
    pay = dict(case["pay"])
    basic = _num(pay.get("basic"))
    da = _num(pay.get("da_amt")) or (basic * _num(pay.get("da_pct")) / 100)
    hra = _num(pay.get("hra_amt")) or (basic * _num(pay.get("hra_pct")) / 100)
    ta = _num(pay.get("travel_allowance"))
    other = _num(pay.get("other_allowance"))
    total = _num(pay.get("total_salary")) or (basic + da + hra + ta + other)
    pay.update({
        "basic_n": basic, "basic_r": C.rupees(basic),
        "da_n": da, "da_r": C.rupees(da),
        "hra_n": hra, "hra_r": C.rupees(hra),
        "ta_r": C.rupees(ta) if ta else "---",
        "other_r": C.rupees(other) if other else "---",
        "total_n": total, "total_r": C.rupees(total),
        "matrix_full": f"{pay.get('level', '')} ({pay.get('matrix', '')})".strip(),
    })
    return pay


def build_context(case_data: dict, blocks: dict | None = None,
                  doc_meta: dict | None = None) -> dict:
    """Assemble the full render context for one document."""
    case = merge_defaults(case_data)
    meta = case["meta"]
    on_date = meta.get("letter_date") or date.today()

    ctx = {
        "meta": meta,
        "school": case["school"],
        "office": case["office"],
        "emp": build_employee(case),
        "pay": build_pay(case),
        "bank": case["bank"],
        "svc": build_service(case),
        "tbl": build_tables(case, on_date),
        "refs": case.get("refs", []),
        "chk": case["checklist"],
        "raw": case,
        "t": blocks or {},
        "doc": doc_meta or {},
        # convenience shorthands used all over the forms
        "today": C.fmt_date(date.today()),
        "letter_date": C.fmt_date(meta.get("letter_date")),
        "letter_date_mr": C.fmt_date_dev(meta.get("letter_date")),
        "place": meta.get("place", ""),
        "place_mr": meta.get("place_mr") or meta.get("place", ""),
    }
    return ctx
