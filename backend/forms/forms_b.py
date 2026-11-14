# -*- coding: utf-8 -*-
"""Forms 10-18: certificates, Form 15, history of service, annexure II and nominations."""
from docxbuild import Doc, rotate_cell_text

from .common import MR, loop_end, loop_start, sr_no

FORMS = []


def form(**meta):
    def wrap(fn):
        meta["build"] = fn
        FORMS.append(meta)
        return fn
    return wrap


# ==========================================================================
# 10. To whomsoever it may concern - GPF member, not NPS
# ==========================================================================
@form(
    code="gpf_not_nps_certificate", order=10,
    title_en="To Whomsoever It May Concern - GPF member, not NPS/DCPS",
    title_mr="प्रमाणपत्र - भ.नि.नि. सदस्य, राष्ट्रीय निवृत्तीवेतन योजनेत नाही",
    language="en",
    blocks=[
        ("heading", "Heading", "TO WHOMSOEVER IT MAY CONCERN", False),
        ("body", "Body - opening", "This is to certify that", True),
        ("body_2", "Body - after the name", "was appointed", True),
        ("body_3", "Body - after the appointment date",
         "on un-aided basis. School divisions and post is Granted 100% from", True),
        ("body_4", "Body - after the aided date",
         "He/She was Member of General Provident Fund Scheme & contributing by", True),
        ("body_5", "Body - after the GPF number",
         "in his/her entire aided service. DCPS / NPS Scheme Number was not allotted to", True),
        ("body_6", "Body - claim sentence",
         "Hence claim of Rs.10,00,000/- was not paid to him/her.", True),
        ("para_2", "Second paragraph",
         "was Member of General Provident Fund (GPF) Scheme and not the member of National Pension Scheme / Defined Contributory Pension Scheme.", True),
        ("closing", "Closing line", "This is for your kind information.", True),
        ("place_label", "Place label", "Place  :", False),
        ("date_label", "Date label", "Date   :", False),
        ("sig_hm", "Left signature caption", "H.M.", False),
        ("sig_eo", "Right signature caption", "E.O.", False),
    ],
)
def build_gpf_certificate(d: Doc):
    d.para("{{ t.heading }}", align="center", size=13, space_after=10)
    d.para([("{{ t.body }}  ", {}),
            ("{{ emp.name_en }}", {"bold": True}),
            (", {{ emp.designation_en }} ", {}),
            ("{{ t.body_2 }} ", {}),
            ("{{ emp.doj_unaided_f }} ", {"bold": True}),
            ("{{ t.body_3 }} ", {}),
            ("{{ emp.doj_aided_f }}. ", {"bold": True}),
            ("{{ t.body_4 }} ", {}),
            ("GPF No.{{ bank.gpf_no }} ", {"bold": True}),
            ("{{ t.body_5 }} ", {}),
            ("{{ emp.name_en }}. ", {"bold": True}),
            ("{{ t.body_6 }}", {})],
           size=12, align="justify", first_line=1.4, line_spacing=2.0)
    d.para([("Further ", {}),
            ("{{ emp.name_en }} ", {"bold": True}),
            ("{{ t.para_2 }}", {})],
           size=12, align="justify", first_line=1.4, line_spacing=2.0)
    d.para("{{ t.closing }}", size=12, first_line=1.4, space_after=16)
    d.para("{{ t.place_label }} {{ meta.place }}", size=12)
    d.para("{{ t.date_label }} {{ letter_date }}", size=12, space_after=4)
    w = d.content_cm
    t = d.table([w * 0.34, w * 0.33, w * 0.33], borders=False)
    d.row(t, ["", "{{ t.sig_hm }}", "{{ t.sig_eo }}"], size=10,
          aligns=["left", "center", "center"])


# ==========================================================================
# 11. Undertaking (vachanpatra) - Marathi
# ==========================================================================
@form(
    code="undertaking_vachanpatra", order=11,
    title_en="Undertaking (Vachanpatra) - refund of excess payment",
    title_mr="वचनपत्र - अतिप्रदानाची रक्कम परत करण्याबाबत",
    language="mr",
    blocks=[
        ("gr_number", "Government circular number at the top",
         "शासन परिपत्रक क्रमांक : वेतन-1221/प्र.क्र.119/टीएनटी-3", False),
        ("gr_sub", "Circular reference under the rule",
         "( शासन परिपत्रक, शालेय शिक्षण व क्रीडा विभाग, क्रमांक वेतन-1021/प्र.क्र.119/टीएनटी-3,\nदिनांक – 22.12.2021 चे सहपत्र)", True),
        ("heading", "Heading", "वचनपत्र", False),
        ("body", "Body - opening", "मी, श्री./श्रीमती", True),
        ("body_2", "Body - after the name", ", पदनाम –", True),
        ("body_3", "Body - main text",
         "या माध्यमिक शाळेत या पदावर कार्यरत होतो. मला शासनाकडून कोणत्याही प्रसंगी जसे की, माझी सेवेत नव्याने नियुक्ती होईल तेंव्हा किंवा अन्य प्रकारे वेतननिश्चिती / वेतनवाढी अथवा इतर कोणत्याही आर्थिक लाभाच्या / प्रदानाच्या अनुषंगाने माझ्या संपूर्ण सेवा कालावधीत, नियमानुसार अथवा कायद्यानुसार देय व अनुज्ञेय ठरत नसतांना (Excess of entitlements), अतिरिक्त रक्कम प्रदान झाल्याची बाब सद्य:स्थितीत/ भविष्यात शासनाच्या निदर्शनास आली/असल्यास, याद्वारे मी असे वचनपत्र देतो की, परिगणनेतील त्रुटीमुळे अथवा कोणत्याही कारणास्तव सदर रकमेमध्ये काही जादा रकमेचे प्रदान केल्याचे सद्य:स्थितीत/भविष्यात शासनाच्या निदर्शनास आल्यास अशी अतिप्रदानाची रक्कम शासनास समायोजन/रोख स्वरुपात परत करण्यास मी न चुकता बांधील आहे/राहील.", True),
        ("place_label", "Place label", "ठिकाण :", False),
        ("date_label", "Date label", "दिनांक :", False),
        ("sign_label", "Signature label", "सही,", False),
        ("name_label", "Name label", "नाव-", False),
        ("desig_label", "Designation label", "पदनाम-", False),
    ],
)
def build_undertaking(d: Doc):
    d.para("{{ t.gr_number }}", size=11, font=MR)
    d.rule()
    d.para("{{ t.gr_sub }}", size=11, font=MR, align="center", space_after=14)
    d.para("{{ t.heading }}", size=13, font=MR, align="center", space_after=14)
    d.para([("{{ t.body }} ", {}),
            ("{{ emp.name_mr }}", {"bold": True}),
            ("{{ t.body_2 }} ", {}),
            ("{{ emp.designation_mr }}, {{ school.name_mr }} "
             "ता.{{ school.taluka_mr }}, जि.{{ school.district_mr }}. ", {"bold": True}),
            ("{{ t.body_3 }}", {})],
           size=13, font=MR, align="justify", first_line=1.6, line_spacing=2.0,
           space_after=16)
    w = d.content_cm
    t = d.table([w * 0.45, w * 0.55], borders=False)
    d.row(t, ["{{ t.place_label }} {{ meta.place_mr }}\n{{ t.date_label }} {{ letter_date }}",
              "{{ t.sign_label }}\n{{ t.name_label }} {{ emp.name_mr }}\n"
              "{{ t.desig_label }}{{ emp.designation_mr }}"],
          size=12, font=MR, valign="top", aligns=["left", "center"])


# ==========================================================================
# 12. Annexure I / Form 15 - application for pension or gratuity
# ==========================================================================
@form(
    code="annexure_1_form_15", order=12, margin_cm=1.3,
    title_en="Annexure I / Form No. 15 - Application for Pension or Gratuity & DCRG",
    title_mr="परिशिष्ट १ / नमुना १५ - निवृत्तीवेतन व उपदान अर्ज",
    language="en",
    blocks=[
        ("heading", "Heading", "ANNEXURE I", False),
        ("form_no", "Form number", "FORM  No. 15", False),
        ("rule_ref", "Rule reference", "(See Rule 198, 198- A, 207, 207-B, 209 and 212)", False),
        ("subheading", "Sub-heading",
         "APPLICATION  FOR   PENSION OR GRATUITY & DEATH-CUM-RETIREMENT GRATUITY", False),
        ("govt_service_note", "Governments under which service rendered",
         "IN NON GOVERNMENT SECONDARY SCHOOLS RECOGNISED BY THE EDUCATION DEPARTMENT OF MAHARASHTRA STATE.", True),
        ("note", "Note under the fingerprint grid",
         "Note – Person who at their option send along with this application certified copies of passport photographs are exempted recording their left hand thumb and finger impressions if they are literate enough to sign their names in English, Hindi or the official regional language.", True),
        ("signatory", "Signatory caption", "Signature of the Head", False),
    ],
)
def build_form_15(d: Doc):
    d.para("{{ t.heading }}", align="center", size=11, bold=True, underline=True)
    d.para("{{ t.form_no }}", align="center", size=11)
    d.para("{{ t.rule_ref }}", align="center", size=10)
    d.para("{{ t.subheading }}", align="center", size=10, space_after=3)

    w = d.content_cm
    t = d.table([1.1, w * 0.50, w - 1.1 - w * 0.50])

    def row(num, label, value, indent=False, valign="top"):
        d.row(t, [num, ("    " if indent else "") + label, value], size=8,
              bolds=[False, False, True], aligns=["center", "left", "left"], valign=valign)

    row("1)", "Name of the Applicant (In block letters)", ": {{ emp.name_en_upper }}")
    row("2)", "Father's Name (and also .. husband's name in case of woman teacher)",
        ": {{ emp.father_name_en }}")
    row("3)", "Religion and  Nationality (In block letters)",
        ": {{ emp.religion_caste }}, {{ emp.nationality }}")
    row("4)", "Permanent residential address showing village/ Town, District and State "
              "(In block letters)", ": {{ emp.address_block }}")
    row("", "a) Address of residence where it is proposed to reside after retirement",
        ": AS ABOVE", indent=True)
    row("5)", "Present or last appointment including Name of establishment",
        ": {{ emp.designation_en_upper }},\n  {{ school.name_en }}")
    row("", "a) Present or last substantive appointment", ": {{ emp.designation_en_upper }}",
        indent=True)
    row("6)", "Date of beginning of service", ": {{ emp.doj_combined }}")
    row("7)", "Date of ending of Service", ": {{ emp.dor_f }}")
    row("", "a) Total of Military Service. Date of commencement an end of each period of "
            "Military service. Amount & nature of any pension / gratuity received for  "
            "Military Service.", ": {{ raw.service.military_service }}", indent=True)
    row("", "b) Governments under which service has been rendered in order of employment",
        ": {{ t.govt_service_note }}", indent=True)
    row("8)", "Length of Service with details, interruptions & non qualifying period "
              "…(100% aided Service)",
        ": {{ svc.net.y }}  Years  {{ svc.net.mm }}  Months  {{ svc.net.dd }}  Days.")
    row("9)", "Class of pension and gratuity applied for And cause of application",
        ": {{ meta.class_of_pension|upper }}")
    row("10)", "Pensionable pay/ Last Pay", ": Rs.    {{ svc.last_pay_r }}")
    row("11)", "Proposed pension", ": Rs.      ---")
    row("12)", "Proposed service Gratuity Death-cum-retirement Gratuity",
        ": Rs.    {{ svc.dcrg_r }}")
    row("", "a) Proposed family pension", ": Rs.      ---", indent=True)
    row("13)", "Date from which pension is to commence", ":         ---")
    row("14)", "Place of payment (Government Treasury or sub Treasury)", ": {{ office.treasury }}")
    row("", "a) Pension rules opted eligible", ": ELIGIBLE", indent=True)
    row("", "b) Whether nomination made for", "", indent=True)
    row("", "        (i) Family Pension", ": --", indent=True)
    row("", "        (ii) Death-cum-Retirement", ": Yes", indent=True)
    row("15)", "Date of applicant's birth by Christa era", ": {{ emp.dob_f }}")
    row("16)", "Height", ": {{ emp.height }}")
    row("17)", "Identification Marks",
        ": {% for m in emp.marks_list %}{{ m }}{% if not loop.last %} {% endif %}{% endfor %}")
    row("", "a) Thumb and finger impression", ": Impressed below.", indent=True)
    row("18)", "Date of which the applicant applied for pension",
        ": {{ meta.application_date|dt }}")

    d.blank()
    fingers = d.table([w / 5] * 5)
    d.row(fingers, ["Thumb", "Fore finger", "Middle finger", "Ring finger", "Little finger"],
          size=10, align="center")
    tr = d.row(fingers, [""] * 5, size=10)
    for cell in tr.cells:
        for _ in range(4):
            d.cell_para(cell, "", size=10)

    d.para("{{ t.note }}", size=9, align="justify", space_before=3)
    d.blank(2)
    d.para("{{ t.signatory }}", size=10, align="right")


# ==========================================================================
# 13. History of Service (landscape)
# ==========================================================================
@form(
    code="history_of_service", order=13, margin_cm=1.1,
    title_en="History of Service (showing interruptions)",
    title_mr="सेवा इतिहास",
    language="en", landscape=True,
    blocks=[
        ("heading", "Heading", "HISTORY OF SERVICE (Showing interruptions) of", False),
        ("dob_label", "Date of birth label (top right)", "DATE OF BIRTH-", False),
        ("audit_head", "Last column heading", "Remarks by the Audit Office", True),
        ("continued", "Continuation note", "Contd on page No.2..", False),
        ("total_label", "Totals - rendered service", "Total Rendered Service", False),
        ("nonq_label", "Totals - non qualifying", "Non Qualifying Service", False),
        ("netq_label", "Totals - net qualifying", "Net Qualifying Service", False),
        ("place_label", "Place label", "Place-", False),
        ("date_label", "Date label", "Date  -", False),
        ("signatory", "Signatory caption", "Head Master", False),
    ],
)
def build_history_of_service(d: Doc):
    d.para([("{{ t.heading }}", {"bold": True}),
            ("\t\t\t\t\t\t", {}),
            ("{{ t.dob_label }} {{ emp.dob_f }}", {"bold": True})], size=10)
    d.para("{{ emp.name_en_upper }}, {{ emp.designation_en_upper }},", size=10, bold=True)
    d.para("{{ school.name_en }}", size=10, bold=True, space_after=3)

    w = d.content_cm
    # Ten columns, as on the original sheet -- the last is the audit office's.
    widths = [4.4, 2.2, 1.9, 2.2, 2.2, 2.1, 2.1, 4.2, 1.5, 1.7]
    scale = w / sum(widths)
    widths = [x * scale for x in widths]
    t = d.table(widths)

    # The two service-period columns carry a "Y | M | D" strip under their
    # heading, so the header is two rows with the other columns merged down.
    titles = ["Establishment", "Appointment", "Pay", "Date of Beginning", "Date of Ending",
              "Total Period of Service", "Duty Period Counting for Pension",
              "Remarks", "How Verified", "{{ t.audit_head }}"]
    d.row(t, titles, size=8, align="center", valign="center", header=True)
    d.row(t, ["", "", "", "", "", "Y  |  M  |  D", "Y  |  M  |  D", "", "", ""],
          size=8, align="center", valign="center", header=True)
    for column in (0, 1, 2, 3, 4, 7, 8, 9):
        t.cell(0, column).merge(t.cell(1, column))

    loop_start(d, t, "r in tbl.service_history", 10)
    d.row(t, ["{{ r.establishment }}", "{{ r.appointment }}",
              "{{ r.pay }}\n{{ r.grade_pay }}", "{{ r.frm_f }}", "{{ r.to_f }}",
              "{{ r.total }}", "{{ r.duty }}", "{{ r.remarks }}", "{{ r.verified }}",
              "{{ r.audit_remarks }}"],
          size=7.5, valign="top", space=0,
          aligns=["left", "left", "center", "center", "center", "center", "center",
                  "left", "center", "left"])
    loop_end(d, t, 10)

    for label, value in (("{{ t.total_label }}", "{{ svc.rendered.dashed }}"),
                         ("{{ t.nonq_label }}", "{{ svc.non_qualifying.dashed }}"),
                         ("{{ t.netq_label }}", "{{ svc.net.dashed }}")):
        tr = d.row(t, [label, "", "", "", "", value, value, "", "", ""],
                   size=8, bold=True, aligns=["right"] + ["center"] * 9)
        d.merge_row(tr, 0, 4)

    d.blank()
    d.two_col("{{ t.place_label }} {{ meta.place }}\n{{ t.date_label }} {{ letter_date }}",
              "{{ t.signatory }}", size=10, right_align="center")


# ==========================================================================
# 14. Annexure II - remarks by the receiving authority
# ==========================================================================
@form(
    code="annexure_2", order=14, margin_cm=1.3,
    title_en="Annexure II - Remarks by Receiving Authority & sanction order",
    title_mr="परिशिष्ट २ - स्वीकृती प्राधिकाऱ्याचा अभिप्राय",
    language="en",
    blocks=[
        ("heading", "Heading", "ANNEXURE II", False),
        ("subheading", "Sub-heading", "(a)          Remarks by Receiving Authority", False),
        ("q1", "Question 1", "As to character and past conduct of applicant", True),
        ("q2", "Question 2", "Explanation of any suspension or degradation", True),
        ("q3", "Question 3", "Regarding any gratuity or pension already received by applicant", True),
        ("q4", "Question 4", "Any other remarks", True),
        ("q5", "Question 5",
         "Specific opinion of the receiving authority whether the service claim is established and should be admitted or not (See rule 98- A ii) 207 –B (a) (ii)", True),
        ("a1", "Answer 1", "Good", False),
        ("a2", "Answer 2", "Nil", False),
        ("a3", "Answer 3", "No", False),
        ("a4", "Answer 4", "Nil", False),
        ("a5", "Answer 5", "The Service claim is established and should be admitted", True),
        ("sig_hm", "Left signature", "Head  Master", False),
        ("sig_right", "Right signature", "Signature and Designation of\nthe  Receiving Authority", True),
        ("countersign", "Countersigned block",
         "Countersigned by education Officer\nZilla Parishad District: {{ school.district_en }}", True),
        ("order_b", "Order of the sanctioning authority - opening",
         "b)  Orders of the pension sanctioning authority. The undersigned having satisfied himself that the service of", True),
        ("order_b2", "Order - continuation",
         ", has been thoroughly satisfactory hereby orders that the grant of the full pension and / or gratuity which may be accepted by the Accountant General admissible under the rules. The grant of this pension and / or gratuity shall commence from   ----", True),
        ("held_over", "Held-over amount line",
         "A sum of Rs.  --- Nil ---   on account of  -- Nil-- is to be held over from the Death-cum Retirement Gratuity till the outstanding dues are assessed and adjusted.", True),
        ("or_block", "Alternative (unsatisfactory service) block",
         "OR\nThe undersigned having satisfied himself that the service of Shri.  / Smt.  /Kumari _____________________ has not been thoroughly satisfactory, hereby orders that the full pension and / or Gratuity which may be accepted by the Accountant General as admissible under the rules  shall be reduced  by the specified amounts or percentage indicated below :", True),
        ("reduction_1", "Reduction line 1", "Amount of the percentage reduction in Pension.", True),
        ("reduction_2", "Reduction line 2", "Amount of the percentage reduction in Gratuity.", True),
        ("reduction_3", "Reduction line 3",
         "The grant of this pension and / or gratuity shall take effect from", True),
        ("treasury_line", "Treasury line",
         "The pension and Death-cum-Retirement Fortuity are payable at", True),
        ("treasury_line_2", "Treasury line end", "Treasury and are chargeable to.", True),
        ("condition", "Condition paragraph",
         "This order is subjected to the condition that should the amount of pension and / or gratuity as authorized by Accountant General be afterwards found to be in excess of the amounts to which the pensioner is entitled under the rules, he / she will be called upon to refund such excess. A declaration from the Government servant accepting this condition has been obtained is enclosed / A declaration from the Government servant accepting this condition has been obtained and submitted separately.", True),
        ("sanction_sig", "Sanctioning authority caption",
         "Signature and Designation of the Authority sanctioning Pension", True),
        ("audit_heading", "Audit enfacement heading", "(a) Audit Enfacement", False),
        ("audit_1", "Audit paragraph 1",
         "Total period of duty/qualifying service which has been accepted for the grant of superannuation  retiring invalid Compensation/Pension/Death-Cum-Retirement Gratuity with reasons for  disallowance's if any other than disallowance's, if any of service  the reasons which are recorded  by the audit  officer on Second/Third Page", True),
        ("note_1", "Note 1",
         "Service for the period commencing from and up to the date of retirement has not yet been verified. This should be done before the pension payment order issued.", True),
        ("note_2", "Note 2",
         "Amount of superannuation/retiring/invalid compensation/Death-Cum-Retirement Gratuity that has been admitted", True),
        ("note_3", "Note 3",
         "Amount of superannuation/retiring/invalid compensation/Death-Cum-Retirement Gratuity admissible after taking into account the reduction in pension and gratuity made by the authority sanctioning Pension.", True),
        ("note_4", "Note 4",
         "The date from which the superannuation/Retiring Pension/Death-Cum-Retirement Gratuity is admissible.", True),
        ("note_5", "Note 5",
         "Head of account to which the superannuation/retiring and special additional Pension/Death Cum-Retirement Gratuity is chargeable", True),
        ("ag_caption", "Accountant General caption", "Accountant General", False),
    ],
)
def build_annexure_2(d: Doc):
    d.para("{{ t.heading }}", align="center", size=11, bold=True, underline=True)
    d.para("{{ t.subheading }}", align="center", size=10, space_after=2)

    w = d.content_cm
    t = d.table([0.9, w * 0.62, w - 0.9 - w * 0.62])
    for idx in range(1, 6):
        d.row(t, [f"{idx})", "{{ t.q" + str(idx) + " }}", ": {{ t.a" + str(idx) + " }}"],
              size=8.5, bolds=[False, False, True], valign="top")

    d.blank(2)
    d.two_col("{{ t.sig_hm }}", "{{ t.sig_right }}", size=9, right_align="left")
    d.para("{{ t.countersign }}", size=9, space_after=4)

    d.para([("{{ t.order_b }} ", {}),
            ("{{ emp.name_en_upper }}, {{ emp.designation_en_upper }}", {"bold": True}),
            ("{{ t.order_b2 }}", {})], size=8.5, align="justify", space_after=4)
    d.para("I     {{ t.held_over }}", size=8.5, align="justify", indent=1.6, space_after=2)
    d.para("{{ t.or_block }}", size=8.5, align="justify", indent=1.0, space_after=2)
    d.para("{{ t.reduction_1 }}", size=8.5, indent=2.4)
    d.para("{{ t.reduction_2 }}", size=8.5, indent=2.4)
    d.para("{{ t.reduction_3 }}", size=8.5, indent=2.4)
    d.para("{{ t.held_over }}", size=8.5, align="justify", indent=2.4, space_after=2)
    d.para([("{{ t.treasury_line }} ", {}),
            ("{{ office.treasury }} ", {"bold": True, "size": 12}),
            ("{{ t.treasury_line_2 }}", {})], size=8.5, align="justify", space_after=4)
    d.para("{{ t.condition }}", size=8.5, align="justify", indent=1.0, first_line=0.8,
           space_after=4)
    d.para("{{ t.sanction_sig }}", size=8.5, align="right", space_after=4)
    d.para("{{ t.audit_heading }}", size=9, align="center")
    d.para("1.    {{ t.audit_1 }}", size=8.5, align="justify", space_after=2)
    d.para([("Note  ", {}), ("1)        {{ t.note_1 }}", {})], size=8.5, align="justify",
           indent=1.0)
    for idx in range(2, 6):
        d.para(f"        {idx})        " + "{{ t.note_" + str(idx) + " }}",
               size=8.5, align="justify", indent=1.0)
    d.blank(2)
    d.para("{{ t.ag_caption }}", size=10, align="right", bold=True)


# ==========================================================================
# 15. Photographs and specimen signatures
# ==========================================================================
@form(
    code="photo_specimen_signature", order=15,
    title_en="Joined photographs and specimen signatures",
    title_mr="छायाचित्र व नमुना स्वाक्षरी",
    language="en",
    blocks=[
        ("sr_no", "Sr. No. printed top-right", "6", False),
        ("photo_label", "Photograph label", "Joined Photographs of", False),
        ("spouse_label", "Spouse label", "& his / her spouse", False),
        ("photo_box", "Text inside the photograph box", "Paste joint photograph here", False),
        ("specimen_label", "Specimen signature label", "Specimen Signatures of", False),
        ("height_label", "Height label", "Height", False),
        ("marks_label", "Identification marks label", "Identification Marks", False),
        ("specimen_heading", "Specimen signature heading", "Specimen Signatures", False),
        ("desig_label", "Designation caption", "Designation –", False),
        ("countersign", "Countersigned block",
         "Education Officer\nZilla Parishad, {{ school.district_en }}", True),
        ("signatory", "Right signature caption", "Head Master", False),
    ],
)
def build_photo_specimen(d: Doc):
    sr_no(d)
    w = d.content_cm
    t = d.table([4.6, w - 4.6], borders=False)
    d.row(t, ["{{ t.photo_label }}", [("{{ emp.name_en_upper }}",
                                       {"bold": True, "underline": True})]], size=11)
    d.row(t, ["{{ t.spouse_label }}", [("{{ emp.spouse_name_en|upper2 }}",
                                        {"bold": True, "underline": True})]], size=11)
    d.blank(2)

    frame = d.table([6.0])
    tr = frame.add_row()
    cell = tr.cells[0]
    # An uploaded photograph drops in here; with none, the box stays empty for
    # a print to be pasted in, as on the original.
    d.cell_para(cell, "{% if photo %}{{ photo }}{% else %}{{ t.photo_box }}{% endif %}",
                reuse_first=True, align="center", size=9)
    for _ in range(6):
        d.cell_para(cell, "", size=11)
    d.blank(2)

    t2 = d.table([4.6, w - 4.6], borders=False)
    d.row(t2, ["{{ t.specimen_label }}",
               ":   {{ emp.name_en_upper }}, {{ emp.designation_en_upper }}"],
          size=11, bolds=[False, True])
    d.blank()
    d.row(t2, ["                  {{ t.height_label }}", ":   {{ emp.height }}"],
          size=11, bolds=[False, True])
    d.blank()
    # Each mark is its own paragraph, so the {%p %} loop has whole paragraphs to repeat.
    d.row(t2, ["{{ t.marks_label }}",
               [[("{%p for m in emp.marks_list %}", {})],
                [("{% if loop.first %}:-  {% else %}      {% endif %}"
                  "{{ loop.index|roman }}) {{ m }}", {})],
                [("{%p endfor %}", {})]]],
          size=11, bolds=[False, True], valign="top")

    d.blank(2)
    d.para("{{ t.specimen_heading }}", size=11, align="center", space_after=8)
    for idx in (1, 2, 3):
        d.para(f"{idx})   ------------------------------------------------------",
               size=11, indent=6.0, space_after=10)
    d.para("{{ t.desig_label }} {{ emp.designation_en }}", size=11, align="center",
           space_after=14)
    d.two_col("{{ t.countersign }}", "{{ t.signatory }}", size=11, right_align="left")


# ==========================================================================
# 16. Declaration for pension / service gratuity
# ==========================================================================
@form(
    code="declaration_service_gratuity", order=16,
    title_en="Declaration for Pension / Service Gratuity and / or DCR Gratuity",
    title_mr="निवृत्तीवेतन / सेवा उपदान घोषणापत्र",
    language="en",
    blocks=[
        ("sr_no", "Sr. No. printed top-right", "7", False),
        ("heading", "Heading", "A Declaration For Pension / Service Gratuity\nand / or D. C. R. Gratuity", True),
        ("body", "Declaration text - opening", "I (Name)", True),
        ("body_2", "Declaration text - after the name",
         "hereby declares that I have neither applied or not received any pension or service gratuity of D. C. R. Gratuity in respect of any portion of the service included in this application and in respect of which pension or gratuity is claimed herein nor shall I submit an application without quoting a reference to this application and the orders in which may be passed thereon.", True),
        ("place_label", "Place label", "Place :", False),
        ("date_label", "Date label", "Date   :", False),
        ("pensioner_sig", "Pensioner signature caption", "Signature of Pensioner", False),
        ("countersign", "Countersigned block",
         "Countersigned by\n\nEducation Officer,\nZilla Parishad.\nDistrict - {{ school.district_en }}", True),
        ("before_me", "Right-hand block", "Before me\n\nSignature\n\nDesignation", True),
    ],
)
def build_declaration_service_gratuity(d: Doc):
    sr_no(d)
    d.para("{{ t.heading }}", align="center", size=11, bold=True, underline=True,
           space_after=12)
    d.para([("{{ t.body }} ", {}),
            ("{{ emp.name_en_upper }}, {{ emp.designation_en_upper }} ",
             {"bold": True, "underline": True}),
            ("{{ t.body_2 }}", {})],
           size=11, align="justify", first_line=1.2, line_spacing=1.7, space_after=16)
    d.para("{{ t.place_label }}   {{ meta.place }}", size=11)
    d.para("{{ t.date_label }} {{ letter_date }}", size=11, space_after=10)
    d.para("({{ emp.name_en }})", size=11, indent=9.0)
    d.para("{{ t.pensioner_sig }}", size=11, indent=9.0, space_after=10)
    d.two_col("{{ t.countersign }}", "{{ t.before_me }}", size=11, right_align="left")


# ==========================================================================
# 17. Nomination for death-cum-retirement gratuity
# ==========================================================================
@form(
    code="nomination_dcrg", order=17,
    title_en="Nomination for Death cum - Retirement Gratuity / Pension",
    title_mr="मृत्यू नि सेवानिवृत्ती उपदान नामनिर्देशन",
    language="en",
    blocks=[
        ("sr_no", "Sr. No. printed top-right", "8", False),
        ("heading", "Heading", "Nomination for Death cum – Retirement Gratuity / Pension", False),
        ("note", "Note under the heading",
         "(When the teacher has been a family and wishes to nominate one member thereof)", True),
        ("body", "Declaration text",
         "I hereby nominate the person mentioned below, who is a member of my family and confer on him/her the right to receive any gratuity / pension that may be sanctioned by Government in the event of my death while in service and the right to receive on my death any gratuity / pension which having become admissible to me on retirement may remain unpaid at my death.", True),
        ("h1", "Column 1 heading", "Name & Address of Nominee", False),
        ("h2", "Column 2 heading", "Relationship with the Teacher", False),
        ("h3", "Column 3 heading", "Age", False),
        ("h4", "Column 4 heading",
         "Contingencies on the happening of which nomination shall become invalid", True),
        ("h5", "Column 5 heading",
         "Name, Address & relationship of the person, if any to whom the right conferred on the nominees shall pass in the event of the nominee predeceasing the Teacher", True),
        ("dated_line", "Dated line", "Dated this", False),
        ("witness_label", "Witness label", "Witness to Signature", False),
        ("servant_sig", "Servant signature caption", "Signature of the Servant", False),
        ("countersign", "Countersigned block",
         "Countersigned by\n\nEducation Officer\nZilla Parishad, {{ school.district_en }}", True),
        ("right_sig", "Right-hand caption", "Signature\nDesignation", True),
    ],
)
def build_nomination(d: Doc):
    sr_no(d)
    d.para("{{ t.heading }}", align="center", size=11, bold=True, underline=True,
           space_after=4)
    d.para("{{ t.note }}", align="center", size=10, space_after=2)
    d.para("{{ t.body }}", size=8.5, align="justify", first_line=1.2, line_spacing=1.5,
           space_after=6)

    w = d.content_cm
    widths = [3.4, 2.4, 1.4, 2.6, w - 9.8]
    t = d.table(widths)
    d.row(t, ["{{ t.h1 }}", "{{ t.h2 }}", "{{ t.h3 }}", "{{ t.h4 }}", "{{ t.h5 }}"],
          size=9, align="center", valign="center", header=True)

    loop_start(d, t, "n in tbl.nominees", 5)
    # The alternate nominees repeat as whole paragraphs inside the last column.
    alternates = [
        [("{%p for a in n.alternates %}", {})],
        [("{{ loop.index }})   {{ a.name }},", {})],
        [("        {{ a.relation }}.", {})],
        [("        B.D- {{ a.dob_f }}", {})],
        [("        Age-{{ a.age }} yrs.            {{ a.share }}", {})],
        [("{%p endfor %}", {})],
    ]
    d.row(t, ["{{ n.name }}\n\n{{ n.address }}", "{{ n.relation }}",
              "{{ n.age }}\nYears", "{{ n.contingency }}", alternates],
          size=9, bold=True, valign="top",
          aligns=["left", "center", "center", "center", "left"])
    loop_end(d, t, 5)

    d.para([("{{ t.dated_line }}  ", {}),
            ("{{ meta.letter_date|dt_long }}", {"bold": True}),
            ("  at  ", {}),
            ("{{ meta.place }}, Tal-{{ school.taluka_en }}, Dist. - {{ school.district_en }}",
             {"bold": True})], size=10, space_before=4, space_after=12)

    d.two_col("{{ t.witness_label }}",
              "({{ emp.name_en_upper }})\n{{ t.servant_sig }}", size=10, right_align="left")
    d.blank()
    for idx in (1, 2):
        d.para(f"{idx})   ---------------------------------", size=10, indent=1.6,
               space_after=10)
    d.two_col("{{ t.countersign }}", "{{ t.right_sig }}", size=10, right_align="left")


# ==========================================================================
# 18. A declaration for pension / gratuity (consent to revision)
# ==========================================================================
@form(
    code="declaration_pension_gratuity", order=18,
    title_en="A Declaration for Pension / Gratuity (consent to revision)",
    title_mr="निवृत्तीवेतन / उपदान घोषणापत्र",
    language="en",
    blocks=[
        ("sr_no", "Sr. No. printed top-right", "9", False),
        ("heading", "Heading", "A Declaration for Pension / Gratuity", False),
        ("body", "Body - opening", "Where as", True),
        ("body_2", "Body - after the sanctioning authority",
         "Region (here state the designation of the officer sanctioning the pension/ family pension/service gratuity /death–cum- retirement gratuity/arrears of pension or gratuity  has consented to grant me the sum of Rs.", True),
        ("body_3", "Body - after the pension amount",
         "a month as the amount of my pension and sum of Rs.", True),
        ("body_4", "Body - after the gratuity amount",
         "as the amount of gratuity / death-cum–retirement gratuity / arrears of pension or  gratuity due to", True),
        ("body_5", "Body - after the name",
         "(here give the name and designation of the servant) I / we fully understand that the pension / family pension / gratuity / death-cum–retirement gratuity/ arrears of pension or gratuity due to", True),
        ("body_6", "Body - closing",
         "is subject to revision on its being found in excess of that to which I am entitled under the rule. I promise to have no objection to such revision and I further promise to repay any amount advanced to me / us in excess of that to which I may be eventually found entitled.", True),
        ("countersign", "Countersigned block",
         "Countersigned by\n\nEducation Officer\nZilla Parishad, {{ school.district_en }}\n\nDistrict: {{ school.district_en|upper }}", True),
        ("hm_sig", "Middle caption", "Sign. Of Head of the School\n& Stamp of the School", True),
        ("pensioner_sig", "Right caption", "Signature of the Pensioner", False),
        ("desig_label", "Designation caption", "Designation-", False),
    ],
)
def build_declaration_pension_gratuity(d: Doc):
    sr_no(d)
    d.para("{{ t.heading }}", align="center", size=11, bold=True, underline=True,
           space_after=12)
    d.para([("{{ t.body }} ", {}),
            ("{{ office.eo_designation_en }} ", {"bold": True}),
            ("{{ t.body_2 }} ", {}),
            ("Nil", {"bold": True, "underline": True}),
            ("  {{ t.body_3 }} ", {}),
            ("{{ svc.dcrg_r }} ", {"bold": True, "underline": True}),
            ("{{ t.body_4 }} ", {}),
            ("{{ emp.name_en_upper }}, {{ emp.designation_en_upper }} ", {"bold": True}),
            ("{{ t.body_5 }} ", {}),
            ("{{ emp.name_en_upper }} ", {"bold": True}),
            ("{{ t.body_6 }}", {})],
           size=11, align="justify", first_line=1.6, line_spacing=1.7, space_after=20)

    w = d.content_cm
    t = d.table([w * 0.33, w * 0.30, w * 0.37], borders=False)
    d.row(t, ["{{ t.countersign }}", "{{ t.hm_sig }}",
              "({{ emp.name_en_upper }})\n{{ t.pensioner_sig }}\n\n"
              "{{ t.desig_label }} {{ emp.designation_en }}"],
          size=10, valign="top", aligns=["left", "left", "left"])
