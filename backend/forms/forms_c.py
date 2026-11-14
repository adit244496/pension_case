# -*- coding: utf-8 -*-
"""Forms 19-27: certificates, pay statements, gratuity calculation and service records."""
from docxbuild import Doc

from .common import MR, letterhead_en, loop_end, loop_start, sr_no

FORMS = []


def form(**meta):
    def wrap(fn):
        meta["build"] = fn
        FORMS.append(meta)
        return fn
    return wrap


# ==========================================================================
# 19. Certificate - no departmental enquiry / no dues
# ==========================================================================
@form(
    code="certificate_no_enquiry", order=19,
    title_en="Certificate - no departmental enquiry pending, no dues",
    title_mr="प्रमाणपत्र - विभागीय चौकशी प्रलंबित नाही",
    language="en",
    blocks=[
        ("sr_no", "Sr. No. printed top-right", "10", False),
        ("heading", "Heading", "CERTIFICATE", False),
        ("body", "Body - opening",
         "This is to certify that no department enquiry is either pending or proposed to be held against", True),
        ("point_2a", "Point 2 (a)",
         "a) No Government or management dues remain to be recovered from him / her", True),
        ("or_label", "'OR' separator", "OR", False),
        ("point_2b", "Point 2 (b) - opening", "b) An amount of Rs.", True),
        ("point_2b_2", "Point 2 (b) - continuation", "still remain to be recovered", True),
        ("point_2b_3", "Point 2 (b) - account line", "from him / her on account of", True),
        ("consent", "Consent sentence",
         "he/she has given / has refused to give his / her written consent for the recovery of this amount from his/her pension and / or gratuity.", True),
        ("countersign", "Countersigned block",
         "Countersigned by\nEducation Officer\nZilla Parishad\nDistrict : {{ school.district_en|upper }}", True),
        ("employer_sig", "Right caption", "Signature of the Employer\nWith Designation", True),
    ],
)
def build_certificate_no_enquiry(d: Doc):
    sr_no(d)
    d.para("{{ t.heading }}", align="center", size=11, bold=True, underline=True,
           space_after=8)
    d.para("{{ t.body }}", size=11, align="justify", indent=1.2, first_line=1.2,
           line_spacing=1.4)
    d.para("{{ emp.name_en_upper }}, {{ emp.designation_en_upper }}.",
           size=11, bold=True, align="center", space_after=6)
    d.para("2)          {{ t.point_2a }}", size=11, space_after=14)
    d.para("{{ t.or_label }}", size=11, align="center", space_after=14)
    d.para([("        {{ t.point_2b }}  ", {}),
            ("____{{ raw.service.dues_recoverable }}____", {}),
            ("  {{ t.point_2b_2 }}", {})], size=11, space_after=10)
    d.para([("{{ t.point_2b_3 }}  --------------- ", {}),
            ("{{ raw.service.dues_recoverable }}", {}),
            (" ---------------------------------------", {})], size=11, space_after=10)
    d.para("{{ t.consent }}", size=11, align="justify", line_spacing=1.4, space_after=18)
    d.para("({{ emp.name_en }})", size=11, indent=9.0, space_after=18)
    d.two_col("{{ t.countersign }}", "{{ t.employer_sig }}", size=11, right_align="left")


# ==========================================================================
# 20. Statement showing the sources of pay drawn
# ==========================================================================
@form(
    code="sources_of_pay", order=20,
    title_en="Statement showing the sources of pay drawn",
    title_mr="वेतनाच्या स्त्रोतांचे विवरणपत्र",
    language="en",
    blocks=[
        ("sr_no", "Sr. No. printed top-right", "11", False),
        ("heading", "Heading", "Statement showing the Sources of pay drawn by", False),
        ("desig_label", "Designation label", "DESIGNATION:", False),
        ("h1", "Column 1 heading", "Date of Beginning", False),
        ("h2", "Column 2 heading", "Date of Ending", False),
        ("h3", "Column 3 heading", "Paid from which Fund", False),
        ("countersign", "Countersigned block",
         "Education Officer\nZilla Parishad\nDistrict-{{ school.district_en }}", True),
        ("signatory", "Right caption", "Head of the School", False),
    ],
)
def build_sources_of_pay(d: Doc):
    sr_no(d)
    d.para("{{ t.heading }}", align="center", size=11, space_after=8)
    d.para([("{{ emp.name_en_upper }}.", {"bold": True, "underline": True}),
            ("            {{ t.desig_label }} ", {}),
            ("{{ emp.designation_en_upper }},", {"bold": True, "underline": True})], size=11)
    d.para([("{{ school.name_en }}", {"bold": True, "underline": True})], size=11)
    d.para([("TAL.{{ school.taluka_en|upper }},   DIST.{{ school.district_en|upper }}",
             {"bold": True, "underline": True}), (" .", {})], size=11, space_after=6)

    w = d.content_cm
    t = d.table([w * 0.26, w * 0.26, w * 0.48])
    d.row(t, ["{{ t.h1 }}", "{{ t.h2 }}", "{{ t.h3 }}"], size=11, align="center", header=True)
    loop_start(d, t, "r in tbl.pay_sources", 3)
    d.row(t, ["{{ r.frm_f }}", "{{ r.to_f }}", "{{ r.fund }}"],
          size=11, bold=True, aligns=["center", "center", "left"], valign="top", space=6)
    loop_end(d, t, 3)
    # a couple of blank rows keep the ruled area tall, as on the printed form
    for _ in range(2):
        d.row(t, ["", "", ""], size=11, space=8)

    d.blank()
    d.two_col("{{ t.countersign }}", "{{ t.signatory }}", size=10, right_align="left")


# ==========================================================================
# 21. Last Pay Certificate
# ==========================================================================
@form(
    code="last_pay_certificate", order=21,
    title_en="Last Pay Certificate",
    title_mr="अंतिम वेतन प्रमाणपत्र",
    language="en",
    blocks=[
        ("sr_no", "Sr. No. printed top-right", "12", False),
        ("heading", "Heading", "Last Pay Certificate", False),
        ("no_label", "Number label", "No.", False),
        ("body", "Body - opening", "Last pay certificate of", True),
        ("desig_label", "Designation label", "Designation", False),
        ("retired_label", "Retirement label", "who is retired on", False),
        ("point_2", "Point 2", "He / She has been paid up to", True),
        ("point_2_end", "Point 2 - end", "at the following rates:", False),
        ("point_3", "Point 3 - opening", "His / Her General Provident Fund A/c. No.", True),
        ("point_3_end", "Point 3 - end", "is maintained by the Pay & P. F. Unit of the Dist.", True),
        ("point_4", "Point 4", "He / She made over charge of the school", True),
        ("point_5", "Point 5",
         "Recoveries are to be made from the pay of the secondary school teacher as detailed on the reverse.", True),
        ("point_6", "Point 6",
         "He / She has been paid leaves salary as detailed below. Deductions have been made as noted on the reverse.", True),
        ("point_7", "Point 7",
         "He is entitled to draw the following up to        ---        as per management's authority Letter No                    .dated        ----", True),
        ("point_8", "Point 8", "He is also entitled to joining time as per rule.", True),
        ("point_9", "Point 9",
         "The details of Income-Tax recovered from him up-to-date from the beginning of the current year are noted on the reverse.", True),
        ("point_10", "Point 10",
         "As per Management's authority Letter No.  -  dated  ----  His/ Her under mentioned L. I. C. Policy / Policies is / are financed from Contributory Provident Fund.", True),
        ("place_label", "Place label", "Place:", False),
        ("date_label", "Date label", "Date  :", False),
        ("countersign", "Countersigned block",
         "Countersigned by\n\nEducation Officer,\nZilla Parishad, {{ school.district_en }}", True),
        ("signatory", "Right caption", "Head of the Institution", False),
    ],
)
def build_last_pay_certificate(d: Doc):
    sr_no(d)
    d.para("{{ t.heading }}", align="center", size=11, bold=True, underline=True)
    d.two_col("{{ t.no_label }}", "Date: {{ letter_date }}", size=11)
    d.para([("{{ t.body }} ", {}), ("{{ emp.name_en_upper }}", {"bold": True})], size=11)
    d.para([("{{ t.desig_label }} ______", {}),
            ("{{ emp.designation_en_upper }}", {"bold": True}),
            ("________ {{ t.retired_label }} ", {}),
            ("{{ emp.dor_f }}", {"bold": True})], size=11)
    d.para([("2)        {{ t.point_2 }}  ", {}),
            ("{{ pay.paid_upto }}", {"bold": True}),
            ("  {{ t.point_2_end }}", {})], size=11, indent=0.6, space_after=6)

    w = d.content_cm
    t = d.table([w * 0.22, w * 0.16, w * 0.40, w * 0.22])
    d.row(t, ["PARTICULARS", "RATE", "PARTICULARS", "RATE"], size=10,
          align="center", header=True)
    rows = [
        ("Substantive Pay", "Rs. {{ pay.basic_r }}",
         "Dearness Allowances (@ {{ pay.da_pct }}%)", "Rs. {{ pay.da_r }}"),
        ("Grade Pay", "Rs.   {{ pay.grade_pay|blank }}",
         "H. R. A. (@ {{ pay.hra_pct }}%)", "Rs. {{ pay.hra_r }}"),
        ("Special Pay", "Rs.    ---", "Trave. Allowance", "Rs. {{ pay.ta_r }}"),
        ("Personal Pay", "Rs.    ---", "Higher Secondary Allowance", "---"),
        ("T. Additional Pay", "Rs.    ---", "P. T. A.\nOther Allowance, if any Deductions",
         "{{ pay.other_r }}"),
        ("", "", "Total Salary", "Rs. {{ pay.total_r }}"),
        ("Income Tax", "Rs.    ---", "General Provi. Fund Rs.    ---", "PLI. Rs.    ---"),
    ]
    for c1, c2, c3, c4 in rows:
        d.row(t, [c1, c2, c3, c4], size=10, valign="center",
              aligns=["left", "left", "left", "left"])

    d.para([("3)        {{ t.point_3 }} ", {}),
            ("{{ bank.gpf_no }}", {"bold": True}),
            (" {{ t.point_3_end }}", {}),
            ("{{ school.district_en }}", {"bold": True}), (" .", {})],
           size=11, indent=0.6, align="justify", space_before=4)
    d.para([("4)        {{ t.point_4 }} ", {}),
            ("{{ school.name_en }}", {"bold": True})],
           size=11, indent=0.6, align="justify")
    d.para("5)        {{ t.point_5 }}", size=11, indent=0.6, align="justify")
    d.para("6)        {{ t.point_6 }}", size=11, indent=0.6, align="justify", space_after=4)

    t2 = d.table([w * 0.42, w * 0.30, w * 0.28])
    d.row(t2, ["PERIOD", "RATE", "AMOUNT"], size=10, align="center", header=True)
    for _ in range(3):
        d.row(t2, ["From      ---      to      ---", "at Rs.   ---", "a month      ---"], size=10)

    for idx in (7, 8, 9, 10):
        d.para(f"{idx})        " + "{{ t.point_" + str(idx) + " }}",
               size=11, indent=0.6, align="justify", space_before=2)

    t3 = d.table([w * 0.18, w * 0.20, w * 0.26, w * 0.18, w * 0.18])
    d.row(t3, ["Policy No.", "Amount", "Due date for the Payment of Premium",
               "Amount of Premium", "Date of Maturity"], size=10, align="center", header=True)
    d.row(t3, ["--", "--", "--", "--", "--"], size=10, align="center")

    d.para("{{ t.place_label }}  {{ meta.place }}", size=11, space_before=6)
    d.para("{{ t.date_label }} {{ letter_date }}", size=11, space_after=6)
    d.two_col("{{ t.countersign }}", "{{ t.signatory }}", size=11, right_align="left")


# ==========================================================================
# 22. Gratuity calculation sheet
# ==========================================================================
@form(
    code="gratuity_calculation", order=22,
    title_en="Gratuity Calculation Sheet",
    title_mr="उपदान गणना पत्रक",
    language="en",
    blocks=[
        ("heading", "Heading", "GRATUITY CALCULATION SHEET", False),
        ("l_name", "Row 1 label", "Name", False),
        ("l_desig", "Row 2 label", "Designation", False),
        ("l_dob", "Row 3 label", "Date of Birth", False),
        ("l_level", "Row 4 label", "Level of Pay in the Pay Matrix", False),
        ("l_basic", "Row 5 label", "Basic Pay", False),
        ("l_entry", "Row 6 label", "Date of entry in the Government service", False),
        ("l_dor", "Row 7 label", "Date of Retirement", False),
        ("l_qualifying", "Row 8 label",
         "Length of qualifying service reckoned for gratuity (100% Aided)", True),
        ("l_break", "Row 8 sub-label", "Period of Break / Without Pay", False),
        ("l_net", "Row 8 sub-label 2", "Net Qualifying Service", False),
        ("l_lastpay", "Row 9 label", "Last Pay for Gratuity", False),
        ("l_formula", "Row 10 label",
         "Retirement gratuity admissible : calculation to be shown as follows : Last Pay / 4 x Qualifying service (in completed six monthly periods, not Exceeding 66)", True),
        ("place_label", "Place label", "Place-", False),
        ("date_label", "Date label", "Date-", False),
        ("signatory", "Signatory caption", "Head Master", False),
    ],
)
def build_gratuity_calculation(d: Doc):
    d.para("{{ t.heading }}", align="center", size=11, bold=True, space_after=6)
    w = d.content_cm
    t = d.table([1.1, w * 0.52, w - 1.1 - w * 0.52])

    def row(num, label, value):
        d.row(t, [num, label, value], size=10, bolds=[False, False, True],
              aligns=["center", "left", "left"], valign="top")

    row("1.", "{{ t.l_name }}", "{{ emp.name_en_upper }}")
    row("2.", "{{ t.l_desig }}", "{{ emp.designation_en_upper }}")
    row("3.", "{{ t.l_dob }}", "{{ emp.dob_f }}")
    row("4.", "{{ t.l_level }}", "{{ pay.level }}\n({{ pay.matrix }})")
    row("5.", "{{ t.l_basic }}", "Rs.{{ pay.basic_r }}")
    row("6.", "{{ t.l_entry }}", "{{ emp.doj_combined }}")
    row("7.", "{{ t.l_dor }}", "{{ emp.dor_f }}")
    row("8.", "{{ t.l_qualifying }}", "{{ svc.gross.words_en }}")
    row("", "{{ t.l_break }}", "{{ svc.non_qualifying.words_en }}")
    row("", "{{ t.l_net }}", "{{ svc.net.words_en }}")
    row("9.", "{{ t.l_lastpay }}", "Rs.{{ svc.last_pay_r }}")
    row("10.", "{{ t.l_formula }}",
        "D.C.R.G.  : {{ svc.dcrg_formula }}\n\n            : Rs.  {{ svc.dcrg_r }}")

    d.blank(2)
    d.two_col("{{ t.place_label }} {{ meta.place }}\n{{ t.date_label }} {{ letter_date }}",
              "{{ t.signatory }}", size=10, right_align="center")


# ==========================================================================
# 23. Statement of leave availed
# ==========================================================================
@form(
    code="leave_statement", order=23,
    title_en="A Statement of Leave Availed",
    title_mr="उपभोगलेल्या रजेचे विवरणपत्र",
    language="en",
    blocks=[
        ("sr_no", "Sr. No. printed top-right", "14", False),
        ("heading", "Heading", "A Statement of Leave Availed By", False),
        ("desig_label", "Designation label", "Designation :", False),
        ("h1", "Column 1 heading", "Nature of Leave", False),
        ("h2", "Column 2 heading", "Period of Leave", False),
        ("h3", "Column 3 heading", "No. of Days", False),
        ("h_from", "Sub-heading From", "From", False),
        ("h_to", "Sub-heading To", "To", False),
        ("wp_label", "Without pay leave row", "Without Pay Leave", False),
        ("lwp_label", "LWP row", "LWP on Medical Ground", False),
        ("no_lwp", "Footer line inside the table",
         "No without pay Leave in the Entire Service", True),
        ("verified", "Verification sentence",
         "The above entries have been verified with reference to the permanent record such as office copies of pay bills etc.", True),
        ("countersign", "Countersigned block",
         "Countersigned by\n\nEducation Officer,\nZilla Parishad,\nDistrict – {{ school.district_en }}", True),
        ("signatory", "Right caption", "Signature", False),
    ],
)
def build_leave_statement(d: Doc):
    sr_no(d)
    d.para("{{ t.heading }}", align="center", size=11, bold=True, underline=True,
           space_after=8)
    d.para([("{{ emp.name_en_upper }}.", {"bold": True, "underline": True})], size=11)
    d.para([("{{ t.desig_label }} ", {}),
            ("{{ emp.designation_en_upper }},", {"bold": True, "underline": True})], size=11)
    d.para([("{{ school.name_en }}", {"bold": True, "underline": True})], size=11, indent=1.2)
    d.para([("TALUKA.{{ school.taluka_en|upper }}, DIST. {{ school.district_en|upper }}",
             {"bold": True, "underline": True})], size=11, indent=1.2, space_after=4)

    w = d.content_cm
    t = d.table([w * 0.30, w * 0.18, w * 0.18, w * 0.34])
    tr = d.row(t, ["{{ t.h1 }}", "{{ t.h2 }}", "", "{{ t.h3 }}"], size=10,
               align="center", header=True)
    d.merge_row(tr, 1, 2)
    d.row(t, ["", "{{ t.h_from }}", "{{ t.h_to }}", ""], size=10, align="center")

    loop_start(d, t, "r in tbl.leave", 4)
    d.row(t, ["{{ r.nature }}", "{{ r.frm_f }}", "{{ r.to_f }}", "{{ r.days_f }}"],
          size=10, aligns=["center", "center", "center", "left"])
    loop_end(d, t, 4)

    d.row(t, ["", "", "", ""], size=10)
    d.row(t, ["{{ t.wp_label }}", "N", "I", "L"], size=10, align="center")
    d.row(t, ["{{ t.lwp_label }}", "N", "I", "L"], size=10, align="center")
    for _ in range(3):
        d.row(t, ["", "", "", ""], size=10)
    tr = d.row(t, ["", "{{ t.no_lwp }}", "", ""], size=10, bold=True, align="center")
    d.merge_row(tr, 1, 2)

    d.para("{{ t.verified }}", size=10, align="justify", first_line=1.2, space_before=4,
           space_after=8)
    d.two_col("{{ t.countersign }}", "{{ t.signatory }}", size=10, right_align="left")


# ==========================================================================
# 24. Family members
# ==========================================================================
@form(
    code="family_members", order=24,
    title_en="Statement showing details of family members",
    title_mr="कुटुंब सदस्यांचा तपशील",
    language="en",
    blocks=[
        ("sr_no", "Sr. No. printed top-right", "15", False),
        ("heading", "Heading", "FAMILY MEMBERS", False),
        ("subheading", "Sub-heading", "Statement showing the Details of Family Members of", False),
        ("desig_label", "Designation label", "Designation:", False),
        ("h1", "Column 1 heading", "Sr. No", False),
        ("h2", "Column 2 heading", "Name of the Family Member", False),
        ("h3", "Column 3 heading", "Date of Birth of the Family Member", True),
        ("h4", "Column 4 heading", "Age In Year", False),
        ("h5", "Column 5 heading", "Relationship with the Pensioner", True),
        ("note", "Note under the table",
         "N. B. :- Information regarding Adults sons / married daughters [expect widow daughters] should not be included in the statement.", True),
        ("place_label", "Place label", "Place  :", False),
        ("date_label", "Date label", "Date   :", False),
        ("countersign", "Countersigned block",
         "Countersigned by\n\nEducation Officer\nZilla Parishad\n\nDistrict :  {{ school.district_en }}", True),
        ("pensioner_sig", "Pensioner caption", "Signature of the Pensioner", False),
        ("hm_sig", "Head master caption", "Signature of the Head of the School", False),
    ],
)
def build_family_members(d: Doc):
    sr_no(d)
    d.para("{{ t.heading }}", align="center", size=11, bold=True, underline=True,
           space_after=6)
    d.para("{{ t.subheading }}", align="center", size=11, space_after=6)
    d.para("{{ emp.name_en_upper }}", size=11, bold=True, indent=1.2)
    d.para([("{{ t.desig_label }} ", {}),
            ("{{ emp.designation_en_upper }}", {"bold": True})], size=11, indent=1.2,
           space_after=4)

    w = d.content_cm
    t = d.table([1.4, w * 0.38, w * 0.20, w * 0.13, w * 0.21])
    d.row(t, ["{{ t.h1 }}", "{{ t.h2 }}", "{{ t.h3 }}", "{{ t.h4 }}", "{{ t.h5 }}"],
          size=10, align="center", valign="center", header=True)
    loop_start(d, t, "f in tbl.family", 5)
    d.row(t, ["{{ f.sr }}.", "{{ f.name|upper2 }}", "{{ f.dob_f }}", "{{ f.age }}",
              "{{ f.relation|upper2 }}"],
          size=10, bold=True, align="center", space=6,
          aligns=["center", "left", "center", "center", "center"])
    loop_end(d, t, 5)

    d.para("{{ t.note }}", size=9, align="justify", space_before=4, space_after=12)
    d.two_col("{{ t.place_label }} {{ meta.place }}\n{{ t.date_label }} {{ letter_date }}",
              "({{ emp.name_en_upper }})\n{{ t.pensioner_sig }}", size=10, right_align="left")
    d.para("{{ t.countersign }}", size=10, space_before=4)
    d.para("{{ t.hm_sig }}", size=10, align="right")


# ==========================================================================
# 25. Form No. 17 - history of breaks in service (landscape)
# ==========================================================================
@form(
    code="form_17_breaks", order=25,
    title_en="Form No. 17 - Statement showing the history of breaks in service",
    title_mr="नमुना १७ - सेवाखंडाचा तपशील",
    language="en", landscape=True,
    blocks=[
        ("heading", "Heading", "Form No. 17", False),
        ("subheading", "Sub-heading", "Statement showing the History of Breaks in Service of", False),
        ("desig_label", "Designation label", "Designation -", False),
        ("school_label", "School label", "School", False),
        ("h1", "Column 1 heading", "Sr.No. of Each Break during the Service", True),
        ("h2", "Column 2 heading", "Name of the Institution in which Break in Service taken place", True),
        ("h3", "Column 3 heading", "Reasons for the Breaks", True),
        ("h4", "Column 4 heading", "Date of Beginning of the Break", True),
        ("h5", "Column 5 heading", "Date of Ending of the Break", True),
        ("h6", "Column 6 heading", "Total Period of the Break", True),
        ("h7", "Column 7 heading",
         "Whether the Break is not intervened by his/her taking up Service in any other capacity (i.e other than a teacher)", True),
        ("h8", "Column 8 heading",
         "Whether the Break is followed by his/her taking up Service in another recognised Secondary School as a teacher", True),
        ("h9", "Column 9 heading",
         "Whether the Break is condoned as per para 7 & 8 of the G.R.E.& S.W.D. No.SSN 3365 G Dated 4/11/68", True),
        ("h10", "Column 10 heading",
         "Break treated as duty period for counting qualifying Service for pension    Y.  M.  D", True),
        ("h11", "Column 11 heading", "Remarks.", False),
        ("nil_marker", "Text printed when there are no breaks", "N  I  L", False),
        ("countersign", "Countersigned block",
         "Education Officer\nZilla Parishad                    District-{{ school.district_en }}", True),
        ("signatory", "Right caption", "Head Master", False),
    ],
)
def build_form_17_breaks(d: Doc):
    d.para("{{ t.heading }}", align="center", size=10, space_after=2)
    w = d.content_cm
    head = d.table([w * 0.62, w * 0.38], borders=False)
    d.row(head, ["{{ t.subheading }}", "{{ t.desig_label }} {{ emp.designation_en_upper }}"],
          size=10, bolds=[False, True], valign="top")
    d.row(head, ["{{ emp.name_en_upper }}", ""], size=10, bolds=[True, False])
    d.row(head, ["{{ t.school_label }}   {{ school.name_en }}", ""], size=10,
          bolds=[True, False], valign="top")
    d.blank()

    widths = [1.6, 2.6, 2.4, 2.2, 2.2, 2.0, 3.0, 3.0, 3.0, 2.6, 2.2]
    scale = w / sum(widths)
    widths = [x * scale for x in widths]
    t = d.table(widths)
    d.row(t, ["{{ t.h" + str(i) + " }}" for i in range(1, 12)],
          size=7, align="left", valign="top", header=True)

    loop_start(d, t, "b in tbl.breaks", 11)
    d.row(t, ["{{ loop.index }}", "{{ b.institution }}", "{{ b.reason }}", "{{ b.frm_f }}",
              "{{ b.to_f }}", "{{ b.total }}", "{{ b.not_intervened }}",
              "{{ b.followed_by }}", "{{ b.condoned }}", "{{ b.treated_as_duty }}",
              "{{ b.remarks }}"], size=8, align="center", valign="top")
    loop_end(d, t, 11)

    # When there are no breaks the printed form carries a struck-through NIL line.
    d.row(t, ["{% if not tbl.breaks %}-----{% endif %}",
              "{% if not tbl.breaks %}--------{% endif %}",
              "{% if not tbl.breaks %}--------{% endif %}",
              "{% if not tbl.breaks %}---- N ----{% endif %}",
              "{% if not tbl.breaks %}---- I ----{% endif %}",
              "{% if not tbl.breaks %}---- L ----{% endif %}",
              "{% if not tbl.breaks %}--------{% endif %}",
              "{% if not tbl.breaks %}--------{% endif %}",
              "{% if not tbl.breaks %}--------{% endif %}",
              "{% if not tbl.breaks %}--------{% endif %}",
              "{% if not tbl.breaks %}--------{% endif %}"],
          size=9, align="center", valign="center", space=14)

    d.blank()
    d.two_col("{{ t.countersign }}", "{{ t.signatory }}", size=10, right_align="left")


# ==========================================================================
# 26. Service certificate
# ==========================================================================
@form(
    code="service_certificate", order=26, margin_cm=1.5,
    title_en="Service Certificate",
    title_mr="सेवा प्रमाणपत्र",
    language="en",
    blocks=[
        ("ref_label", "Reference number label", "Ref No.:", False),
        ("date_label", "Date label", "Date-", False),
        ("heading", "Heading", "SERVICE CERTIFICATE", False),
        ("body", "Body - opening", "This is to certify that Shri /Smt", True),
        ("body_2", "Body - continuation",
         "was working in the following institutions run by", True),
        ("body_3", "Body - after the society name", "as a", True),
        ("body_4", "Body - end",
         "in aided Secondary & Higher Secondary Schools. Period mentioned against each institutions.", True),
        ("recognised", "Recognition sentence",
         "These schools are recognized and aided by the Dept. of Education of Maharashtra State.", True),
        ("h1", "Column 1 heading", "Sr. No", False),
        ("h2", "Column 2 heading", "Name of the Schools", False),
        ("h3", "Column 3 heading", "Designation", False),
        ("h4", "Column 4 heading", "Service Period", False),
        ("h5", "Column 5 heading", "Total Service Y  M  D", True),
        ("h6", "Column 6 heading", "Ramarks.", False),
        ("h_from", "Sub-heading From", "From", False),
        ("h_to", "Sub-heading To", "To", False),
        ("total_rendered", "Totals - rendered", "Total Rendered Service from", False),
        ("total_nonq", "Totals - non qualifying", "Non Qualifying Service", False),
        ("total_netq", "Totals - net qualifying",
         "Net Qualifying Service counted for pension and gratuity", True),
        ("place_label", "Place label", "Place –", False),
        ("date_label2", "Date label (footer)", "Date  –", False),
        ("signatory", "Signatory caption", "Head Master", False),
    ],
)
def build_service_certificate(d: Doc):
    letterhead_en(d, rule=False)
    d.rule()
    d.two_col([("{{ t.ref_label }}{{ meta.letter_ref_no }}", {"italic": True})],
              [("{{ t.date_label }} {{ letter_date }}", {"italic": True})], size=10)
    d.para("{{ t.heading }}", align="center", size=11, bold=True, underline=True,
           italic=True, space_before=6, space_after=6)
    d.para([("{{ t.body }} ", {}),
            ("{{ emp.name_en }}", {"bold": True}),
            (" {{ t.body_2 }} ", {}),
            ("{{ school.society_line_en }} ", {"bold": True}),
            ("{{ t.body_3 }} ", {}),
            ("{{ emp.designation_en }} ", {"bold": True}),
            ("{{ t.body_4 }}", {})],
           size=10, align="justify", first_line=1.2, line_spacing=1.25, space_after=4)
    d.para("{{ t.recognised }}", size=10, align="justify", first_line=1.2, space_after=4)

    w = d.content_cm
    t = d.table([1.2, w * 0.34, 1.9, 2.4, 2.4, w - 1.2 - w * 0.34 - 1.9 - 4.8 - 1.9, 1.9])
    tr = d.row(t, ["{{ t.h1 }}", "{{ t.h2 }}", "{{ t.h3 }}", "{{ t.h4 }}", "",
                   "{{ t.h5 }}", "{{ t.h6 }}"], size=9, align="center", valign="center",
               header=True)
    d.merge_row(tr, 3, 4)
    d.row(t, ["", "", "", "{{ t.h_from }}", "{{ t.h_to }}", "", ""], size=9, align="center")

    loop_start(d, t, "r in tbl.school_service", 7)
    d.row(t, ["{{ loop.index }})", "{{ r.school }}", "{{ r.designation }}", "{{ r.frm_f }}",
              "{{ r.to_f }}", "{{ r.total }}", "{{ r.grant_status }}"],
          size=8, valign="top",
          aligns=["center", "left", "center", "center", "center", "center", "center"])
    loop_end(d, t, 7)

    tr = d.row(t, ["", "{{ t.total_rendered }} {{ emp.doj_unaided_f }} to "
                       "{{ svc.unaided_end_f }} (UN AIDED)", "", "", "",
                   "{{ svc.unaided.dashed }}", ""], size=9, bold=True,
               aligns=["center", "left", "center", "center", "center", "center", "center"])
    d.merge_row(tr, 1, 4)
    tr = d.row(t, ["", "From {{ emp.doj_aided_f }} to {{ emp.dor_f }}  (100% AIDED)", "", "", "",
                   "{{ svc.gross.dashed }}", ""], size=9, bold=True,
               aligns=["center", "left", "center", "center", "center", "center", "center"])
    d.merge_row(tr, 1, 4)
    tr = d.row(t, ["", "{{ t.total_nonq }}", "", "", "", "{{ svc.non_qualifying.dashed }}", ""],
               size=9, bold=True,
               aligns=["center", "left", "center", "center", "center", "center", "center"])
    d.merge_row(tr, 1, 4)
    tr = d.row(t, ["", "{{ t.total_netq }}", "", "", "", "{{ svc.rendered.dashed }}", ""],
               size=9, bold=True,
               aligns=["center", "left", "center", "center", "center", "center", "center"])
    d.merge_row(tr, 1, 4)
    tr = d.row(t, ["", "From {{ emp.doj_aided_f }} to {{ emp.dor_f }}  (100% Aided)  Service",
                   "", "", "", "{{ svc.net.dashed }}", ""], size=9, bold=True,
               aligns=["center", "right", "center", "center", "center", "center", "center"])
    d.merge_row(tr, 1, 4)

    d.blank(2)
    d.two_col("{{ t.place_label }} {{ meta.place }}\n{{ t.date_label2 }} {{ letter_date }}",
              "{{ t.signatory }}", size=10, right_align="center")


# ==========================================================================
# 27. Service (FRA) certificate + no dues - issued by a previous school
# ==========================================================================
@form(
    code="service_fra_certificate", order=27,
    title_en="Service (FRA) Certificate and No Dues Certificate (previous school)",
    title_mr="सेवा (एफ.आर.ए.) प्रमाणपत्र व नादेय प्रमाणपत्र",
    language="en", enabled=False,
    blocks=[
        ("school_label", "School name label", "Name of the School-", False),
        ("condition_line", "Line above the heading",
         "If School or Post: First Unaided or/then Partially Aided or/then 100% Aided. Full Time Recognized & Aided Certificate", True),
        ("heading", "Heading", "SERVICE (FRA) CERTIFICATE", False),
        ("body", "Body - opening", "This is to certify that", True),
        ("body_2", "Body - continuation",
         "was working in this Secondary / Higher Secondary School as a detail below:", True),
        ("h1", "Column 1 heading", "Sr.No.", False),
        ("h2", "Column 2 heading", "Type of Post", False),
        ("h3", "Column 3 heading", "Designation", False),
        ("h4", "Column 4 heading", "From", False),
        ("h5", "Column 5 heading", "To", False),
        ("h6", "Column 6 heading", "Grant status", False),
        ("para_2", "Recognition paragraph",
         "This Secondary / Higher Secondary School was / is recognized and Unaided from June 1999, 60% aided from 01-09-2006, 80% aided from 01-03-2007 & 100% aided from 01-03-2008 by the School Education and Sports Department of Maharashtra State when the said employee was working in this Secondary / Higher Secondary School.", True),
        ("para_3", "Post status paragraph",
         "(During this period the post on which the said teacher / non-teaching staff was working as per above details. He / She is / was Retired / Death on 100% aided post and the concern School / Jr.College is 100% Aided sanctioned by the School Education and Sports Dept. Maharashtra State) and the Post on that the said employee served was partly Aided before 01-11-2005.", True),
        ("verified", "Verification line",
         "Service Verified from Pay Bills, Muster Rolls and found correct.", True),
        ("no_break_mr", "Marathi no-break line", "वरील कालावधीत कोणत्याही प्रकारचा सेवाखंड नाही.", True),
        ("issue_purpose", "Purpose line",
         "This certificate issue only for Death-cum-Retirement Gratuity as per Govt.G.R", True),
        ("gr_1", "GR reference 1", "सेनिप्र-2023/प्र.क्र.57/सेवा-4 दिनांक 24 ऑगस्ट, 2023.", True),
        ("gr_2", "GR reference 2", "संकीर्ण-2024/प्र.क्र. 63/सेवा-4 दिनांक 27 डिसेंबर, 2024.", True),
        ("place_label", "Place label", "Place –", False),
        ("date_label", "Date label", "Date", False),
        ("countersign", "Countersigned block",
         "Countersigned by,\nEducation Officer,\nZilla Parishad, {{ school.district_en }}", True),
        ("hm_sig", "Head master caption", "Head Master", False),
        ("nodues_heading", "No dues heading", "NO DUES CERTIFICATE", False),
        ("nodues_body", "No dues body",
         "This is to certify that, no departmental enquiry is either pending or proposed to be held against that", True),
        ("nodues_body_2", "No dues point 2",
         "2) No Government of management dues remain to be recovered from him an amount of Rs....... ----....... still remains to be recovered from him on A/c of ......... --- .........and he has given/he has refused to give his written consent for the recovery of this amount from his pension and /or gratuity. The written consent is kept among the pension papers.", True),
        ("employee_sig", "Employee signature caption", "Signature of the Employee", False),
    ],
)
def build_fra_certificate(d: Doc):
    d.para([("{{ t.school_label }} ", {}),
            ("{{ raw.meta.previous_school|default(school.name_en) }}", {"bold": True})],
           size=10, space_after=2)
    d.para("{{ t.condition_line }}", align="center", size=9, space_after=4)
    d.para("{{ t.heading }}", align="center", size=11, space_after=4)
    d.para([("{{ t.body }} ", {}),
            ("{{ emp.name_en }}", {"bold": True}),
            (" {{ t.body_2 }}", {})], size=10, align="justify", first_line=1.2,
           space_after=4)

    w = d.content_cm
    t = d.table([1.4, w * 0.16, w * 0.18, w * 0.19, w * 0.19, w - 1.4 - w * 0.72])
    d.row(t, ["{{ t.h1 }}", "{{ t.h2 }}", "{{ t.h3 }}", "{{ t.h4 }}", "{{ t.h5 }}",
              "{{ t.h6 }}"], size=9, align="center", header=True)
    loop_start(d, t, "r in tbl.school_service", 6)
    d.row(t, ["{{ loop.index }}.", "{{ r.post_type|default('Full Time') }}",
              "{{ r.designation }}", "{{ r.frm_f }}", "{{ r.to_f }}", "{{ r.grant_status }}"],
          size=9, bold=True, align="center")
    loop_end(d, t, 6)

    for key in ("para_2", "para_3", "verified"):
        d.para("{{ t." + key + " }}", size=10, align="justify", first_line=1.2,
               space_before=4)
    d.para("{{ t.no_break_mr }}", size=10, font=MR, align="justify", space_before=4)
    d.para("{{ t.issue_purpose }}", size=10, bold=True, space_before=4)
    d.para("1)     {{ t.gr_1 }}", size=10, font=MR, indent=0.6)
    d.para("2)     {{ t.gr_2 }}", size=10, font=MR, indent=0.6, space_after=6)
    d.two_col("{{ t.place_label }} {{ meta.place }}\n{{ t.date_label }} {{ letter_date }}\n"
              "{{ t.countersign }}", "{{ t.hm_sig }}", size=10, right_align="center")

    d.rule()
    d.para("{{ t.nodues_heading }}", align="center", size=11, bold=True, underline=True,
           space_before=4, space_after=4)
    d.para([("{{ t.nodues_body }} ", {}),
            ("{{ emp.name_en }}.", {"bold": True})], size=10, align="justify",
           first_line=1.2, line_spacing=1.4)
    d.para("{{ t.nodues_body_2 }}", size=10, align="justify", line_spacing=1.4,
           space_after=8)
    d.two_col("{{ t.place_label }} {{ meta.place }}\n{{ t.date_label }} -",
              "({{ emp.name_en }})\n{{ emp.designation_en }}\n{{ t.employee_sig }}",
              size=10, right_align="center")
