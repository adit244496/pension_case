# -*- coding: utf-8 -*-
"""Forms 1-9: cover sheet, covering letters, data sheet, Form I and the checklist."""
from docxbuild import Doc

from .common import EN, MR, letterhead_mr, loop_end, loop_start, sr_no

FORMS = []


def form(**meta):
    def wrap(fn):
        meta["build"] = fn
        FORMS.append(meta)
        return fn
    return wrap


# ==========================================================================
# 1. Cover sheet (A.G. copy)
# ==========================================================================
@form(
    code="cover_sheet", order=1,
    title_en="Cover Sheet - Retirement Gratuity (DCRG) Case",
    title_mr="मुखपृष्ठ - सेवानिवृत्ती उपदान प्रकरण",
    language="both",
    blocks=[
        ("heading", "Main heading", "RETIREMENT GRATUITY  (DCRG) CASE", False),
        ("gr_line", "Government resolution line under the heading",
         "(वित्त विभाग शासन परिपत्रक क्र.सेनिप्र.-2023/प्र.क्र.57/सेवा-4 दिनांक 24 ऑगस्ट, 2024 अन्वये)", True),
        ("copy_mark", "Copy marking printed above the box", "A. G. COPY", False),
        ("lbl_name", "Label - Name", "Name", False),
        ("lbl_mobile", "Label - Mobile", "Mobile", False),
        ("lbl_email", "Label - Email", "Email", False),
        ("lbl_desig", "Label - Designation", "Desig.", False),
        ("lbl_address", "Label - Address", "Address", False),
        ("lbl_school", "Label - School name", "Name of the School", False),
        ("lbl_dob", "Label - Date of birth", "Dt. of Birth", False),
        ("lbl_dor", "Label - Date of retirement", "Dt. of Retirement", False),
    ],
)
def build_cover(d: Doc):
    d.para("{{ t.copy_mark }}", align="center", size=16, bold=True, space_after=8)
    cell = d.box()
    d.cell_para(cell, "{{ t.heading }}", reuse_first=True, align="center",
                size=18, bold=True, underline=True, space_after=4)
    d.cell_para(cell, "{{ t.gr_line }}", align="center", size=9, font=MR, space_after=14)

    rows = [
        ("{{ t.lbl_name }}", "{{ emp.name_en_upper }}"),
        ("{{ t.lbl_mobile }}", "{{ emp.mobile }}"),
        ("{{ t.lbl_email }}", "{{ emp.email }}"),
        ("{{ t.lbl_desig }}", "{{ emp.designation_en_upper }}"),
    ]
    for label, value in rows:
        d.cell_para(cell, [(f"{label} : ", {"size": 15}), (value, {"bold": True, "size": 13})],
                    space_after=10)

    d.cell_para(cell, [("{{ t.lbl_address }} : At.- ", {"size": 15}),
                       ("{{ emp.addr_at }}", {"bold": True, "size": 13}),
                       (", POST-", {"size": 15}),
                       ("{{ emp.addr_post }}.", {"bold": True, "size": 13})], space_after=6)
    d.cell_para(cell, [("TAL.- ", {"size": 15}),
                       ("{{ emp.addr_taluka }},", {"bold": True, "size": 13})],
                indent=3.2, space_after=6)
    d.cell_para(cell, [("DIST.- ", {"size": 15}),
                       ("{{ emp.addr_district }}. PIN- {{ emp.addr_pin }}",
                        {"bold": True, "size": 13})], indent=3.2, space_after=12)

    d.cell_para(cell, [("{{ t.lbl_school }} :- ", {"size": 11}),
                       ("{{ school.name_en }}", {"bold": True, "size": 13})], space_after=4)
    d.cell_para(cell, [("TAL.-{{ school.taluka_en }}, DIST.{{ school.district_en }}. "
                        "PIN-{{ school.pin }}", {"bold": True, "size": 13})],
                indent=3.2, space_after=18)

    d.cell_para(cell, [("{{ t.lbl_dob }} - ", {"size": 12}),
                       ("{{ emp.dob_f }}", {"bold": True, "size": 13}),
                       ("\t\t", {}),
                       ("{{ t.lbl_dor }} - ", {"size": 12}),
                       ("{{ emp.dor_f }}", {"bold": True, "size": 13})], space_after=6)


# ==========================================================================
# 2. Covering letter from the school to the Education Officer (Marathi)
# ==========================================================================
@form(
    code="covering_letter", order=2, margin_cm=1.6,
    title_en="Covering letter - School to Education Officer",
    title_mr="सोबतचे पत्र - शाळा ते शिक्षणाधिकारी",
    language="mr",
    blocks=[
        ("ref_label", "Outward number label", "जा.क्र.: माध्य./", False),
        ("date_label", "Date label", "दिनांक:", False),
        ("to_label", "'To' label", "प्रति,", False),
        ("subject", "Subject line", "विषय- सेवानिवृत्ती उपदान (Retirement Gratuity) मंजूर होणे बाबत...", True),
        ("ref_heading", "Reference heading", "संदर्भ-", False),
        ("salutation", "Salutation", "सन्मा.महोदय,", False),
        ("intro", "Opening paragraph (before the numbered points)",
         "उपरोक्त विषयान्वये विनंती की, आमचे विद्यालयातील", True),
        ("intro_2", "Continuation of the opening paragraph",
         "हे आमचे संस्थेमध्ये दिनांक", True),
        ("intro_3", "Opening paragraph - closing sentence",
         "पासून अनुदानित/अंशत: अनुदानीत माध्यमिक विद्यालयात कार्यरत असून त्यांची जन्मदिनांक", True),
        ("intro_4", "Opening paragraph - final sentence",
         "असा असल्याने ते दिनांक", True),
        ("intro_5", "Opening paragraph - end",
         "रोजी नियत वयोमानानुसार सेवानिवृत्त झाले आहेत. त्यांचे सेवानिवृत्ती उपदान (Gratuity) मंजूरी बाबतचे सर्व कागदपत्रे मुळ सेवापुस्तकासह सोबत सादर करीत आहे.", True),
        ("point_1", "Point 1 - pay fixation verification",
         "सुधारीत वेतनश्रेणी 5वा वेतन आयोग {{ emp.doj_unaided_f }}, 6वा वेतन आयोग 01/01/2006, 7वा वेतन आयोग 01/01/2016 व कालबद्ध पदोन्नती यामधील वेतननिश्चितीच्या पडताळणी झालेली असून सेवापुस्तकात त्यांच्या नोंदी आहेत.", True),
        ("point_2", "Point 2 - continuous service, no break",
         "यांची दिनांक {{ emp.doj_unaided_f }} (UN AIDED), {{ emp.doj_aided_f }} (100% AIDED) ते {{ emp.dor_f }} अखेर सलग सेवा असून त्यांचे सेवेमध्ये कोणत्याही प्रकारचा सेवाखंड नाही.", True),
        ("point_3", "Point 3 - un-aided period contribution",
         "यांची दिनांक {{ emp.doj_unaided_f }} ते {{ svc.unaided_end_f }} अखेर विना अनुदानीत/अंशत: विना अनुदानीत सेवा असून सदर कालावधीत व्यवस्थापनाने अंशदायी भविष्य निर्वाह निधी खाते सुरुच केलेले नसल्यामुळे शालेय शिक्षण व क्रीडा विभाग परिपत्रक क्रमांक: एसएनएसएन 1007/(321/07)/माशि-2, मंत्रालय विस्तार भवन, मुंबई-400 032 दिनांक 08 एप्रिल, 2008 अन्वये विनाअनुदानीत कालावधीतील अंशदायी भविष्यनिर्वाह निधीतील वर्गणीची रक्कम व्याजासहीत शासकीय कोषागारात भरण्याचा प्रश्न उदभवत नाही.", True),
        ("point_4", "Point 4 - proposal forwarded as per GR",
         "यांची 100% अनुदानीतवरील नियुक्ती 1 नोव्हेंबर, 2005 नंतरची असल्यामुळे शालेय शिक्षण विभाग शासन निर्णय दि.14 जून, 2023 व 24 ऑगस्ट, 2023 नुसार त्यांच्या सेवानिवृत्ती उपदान (DCRG) मंजूरी बाबतचा प्रस्ताव शासन निर्णयातील कार्यपध्दती नुसार सोबत पाठवित आहे.", True),
        ("closing", "Closing request",
         "तरी कृपया सेवानिवृत्ती उपदान मंजूरी बाबत योग्य ती कार्यवाही व्हावी, ही विनंती.", True),
        ("regards", "Sign-off", "कळावे.\nआपला विश्वासू", True),
        ("signatory", "Signatory caption", "मुख्याध्यापक", False),
        ("enclosure", "Enclosure line",
         "सोबत- सेवानिवृत्ती उपदान प्रस्ताव मुळ सेवापुस्तकासह", True),
    ],
)
def build_covering_letter(d: Doc):
    letterhead_mr(d)
    d.two_col("{{ t.ref_label }}{{ meta.letter_ref_no }}",
              "{{ t.date_label }} {{ letter_date }}", size=12)
    d.para("{{ t.to_label }}", size=12, font=MR, space_before=8)
    d.para("{{ office.addressee_mr }}", size=12, font=MR, indent=1.6)
    d.para([("{{ t.subject }}", {"bold": True})], size=12, font=MR, indent=1.6,
           space_before=8)
    d.para("{{ emp.name_mr }}, {{ emp.designation_mr }}", size=12, font=MR,
           bold=True, indent=2.6, space_after=6)

    # References are a list on the case, printed 1) 2) 3) ...
    d.para([("{{ t.ref_heading }} ", {"bold": True}),
            ("{%p for r in refs %}", {})], size=12, font=MR, indent=1.6)
    d.para("{{ loop.index }}) {{ r }}", size=12, font=MR, indent=2.6)
    d.para("{%p endfor %}", size=6)
    d.para("{{ t.salutation }}", size=12, font=MR, space_before=6)
    d.para([("{{ t.intro }} ", {}),
            ("{{ emp.name_mr }}, {{ emp.designation_mr }} ", {"bold": True}),
            ("{{ t.intro_2 }} ", {}),
            ("{{ emp.doj_unaided_f }} (UN AIDED), {{ emp.doj_aided_f }} (100% AIDED) ",
             {"bold": True}),
            ("{{ t.intro_3 }} ", {}),
            ("{{ emp.dob_f }} ", {"bold": True}),
            ("{{ t.intro_4 }} ", {}),
            ("{{ emp.dor_f }} ", {"bold": True}),
            ("{{ t.intro_5 }}", {})],
           size=10.5, font=MR, align="justify", first_line=1.0, line_spacing=1.06,
           space_after=4)

    for idx in range(1, 5):
        d.para([(f"{idx}.  ", {"bold": True}),
                ("{{ emp.name_mr }}, {{ emp.designation_mr }} ", {"bold": True}),
                ("{{ t.point_" + str(idx) + " }}", {})],
               size=10.5, font=MR, align="justify", indent=1.0, line_spacing=1.06,
               space_after=4)

    d.para("{{ t.closing }}", size=10.5, font=MR, align="justify",
           first_line=1.0, space_after=6)
    d.para("{{ t.regards }}", size=11, font=MR, align="right", space_after=10)
    d.para("{{ t.signatory }}", size=11, font=MR, align="right", space_after=10)
    d.para("{{ t.enclosure }}", size=11, font=MR)


# ==========================================================================
# 3. Annexure A - Departmental Data Sheet
# ==========================================================================
@form(
    code="annexure_a_data_sheet", order=3,
    title_en="Annexure A - Departmental Data Sheet",
    title_mr="परिशिष्ट अ - विभागीय माहिती पत्रक",
    language="en",
    blocks=[
        ("sr_no", "Sr. No. printed top-right", "24", False),
        ("heading", "Heading", "Annexure A  -  Deprtmental Data Sheet", False),
        ("signatory", "Signature caption", "Signature of the\nPay & Pro. Fund Unit", True),
    ],
)
def build_annexure_a(d: Doc):
    sr_no(d)
    d.para("{{ t.heading }}", align="center", size=13, bold=True, space_after=8)

    w = d.content_cm
    # -- DDO code / class of pension -------------------------------------
    t1 = d.table([3.6, w * 0.33, 3.4, w - 3.6 - w * 0.33 - 3.4])
    d.row(t1, ["10Digit DDO Code", "{{ school.ddo_code|spaced }}", "Class of Pension",
               "{{ meta.class_of_pension }}"],
          size=10, aligns=["left", "center", "left", "left"],
          bolds=[False, True, False, True])

    t2 = d.table([w * 0.62, 2.2, w * 0.38 - 2.2])
    d.row(t2, ["Name : {{ emp.name_en_upper }}", "Sex :", "{{ emp.sex }}"],
          size=10, bolds=[True, False, True])
    d.row(t2, ["Designation : {{ emp.designation_en_upper }}", "Group / Class",
               "{{ emp.group_class }}"], size=10, bolds=[True, False, True])

    t3 = d.table([w / 2, w / 2])
    d.row(t3, ["a) Address Before Retirement :", "b) Address After Retirement :"], size=10)
    d.row(t3, ["{{ school.name_en }}\nTAL.{{ school.taluka_en }}, DIST.{{ school.district_en }}",
               "{{ emp.address_block }}\nMOBILE NO.-{{ emp.mobile }}"],
          size=10, bold=True, valign="top")

    t4 = d.table([5.4, w - 5.4])
    for label, value in (
        ("Department :", "{{ school.department_en }}"),
        ("Place / District of Retirement :", "{{ school.district_en }}"),
        ("DDO Retired From :", "{{ office.zp_district_en }}"),
    ):
        d.row(t4, [label, value], size=10, bolds=[False, True])

    t5 = d.table([4.0, w * 0.36, 4.0, w - 4.0 - w * 0.36 - 4.0])
    d.row(t5, ["T.O. for Pension :", "{{ office.to_pension }}", "T.O. for DCRG:",
               "{{ office.to_dcrg }}"], size=10, bolds=[False, True, False, True])

    t6 = d.table([5.4, w - 5.4])
    d.row(t6, [[("Bank Details :", {"bold": True, "underline": True})], ""], size=10)
    for label, value in (
        ("a) Bank Name :", "{{ bank.name }}"),
        ("b) Bank Branch :", "{{ bank.branch_address }}"),
        ("c) Bank A/C No. :", "{{ bank.account_no|spaced }}"),
    ):
        d.row(t6, [label, value], size=10, bolds=[False, True])

    t7 = d.table([w * 0.55, w * 0.45])
    d.row(t7, ["GPF Account No. allotted by A.G.Office :", "{{ bank.gpf_no }}"],
          size=10, bolds=[False, True])
    d.row(t7, ["Date of Birth : {{ emp.dob_f }}",
               "Date of Appointment :\n{{ emp.doj_combined }}"],
          size=10, bold=True, valign="top")
    d.row(t7, ["Date of Commencement of pensionable Service :\n{{ emp.doj_combined }}",
               "Date of Retirement : {{ emp.dor_f }}"],
          size=10, bold=True, valign="top")

    t8 = d.table([w * 0.62, w * 0.38])
    for label, value in (
        ("Date of medical certificate invalidating government Servant", "Nil"),
        ("Date of lodging FIR in absconding cases", "Nil"),
        ("Period of Foreign Service", "{{ raw.service.foreign_service }}"),
        ("Whether contributions received for the above period :",
         "{{ raw.service.foreign_contribution }}"),
        ("Length of Military Service, if any :", "{{ raw.service.military_service }}"),
        ("Amount of Military Pension / Gratuity if any", "{{ raw.service.military_pension }}"),
    ):
        d.row(t8, [label, value], size=10, bolds=[False, True])

    t9 = d.table([w * 0.40, w * 0.20, w * 0.20, w * 0.20])
    d.row(t9, ["", "Year", "Months", "Days"], size=10, align="center", header=True)
    for label, key, dash_when_nil in (
        ("Gross Service :  (100% Aided)", "svc.gross", False),
        ("Non - Qualifying Service :", "svc.non_qualifying", True),
        ("Weightage", "svc.weightage", True),
        ("Net Qualifying Service :", "svc.net", False),
    ):
        p = "d" if dash_when_nil else ""
        # dyy/dmm/ddd render "--" for a nil period, as the original does.
        d.row(t9, [label,
                   "{{ " + key + "." + p + "yy }}",
                   "{{ " + key + "." + p + "mm }}",
                   "{{ " + key + "." + p + "dd }}"],
              size=10, aligns=["left", "center", "center", "center"],
              bolds=[False, True, True, True])

    t10 = d.table([w * 0.34, w * 0.44, w * 0.22])
    d.row(t10, ["Average Emoluments", "Last Pay drawn", "{{ svc.last_pay_r }}"],
          size=10, aligns=["left", "center", "right"], bolds=[False, True, True])
    d.row(t10, ["Non-Practicing Allowance", "", "{{ pay.npa|blank }}"],
          size=10, aligns=["left", "center", "right"])
    d.row(t10, ["Other Allowances", "Total of pay", "{{ svc.last_pay_r }}"],
          size=10, aligns=["left", "center", "right"], bolds=[False, True, True])

    d.blank(3)
    d.para("{{ t.signatory }}", align="center", size=11)


# ==========================================================================
# 4. Form 2 - letter to the Accounts Officer
# ==========================================================================
@form(
    code="form_2_accounts_officer", order=4,
    title_en="Form 2 - Letter to the Accounts Officer forwarding gratuity papers",
    title_mr="नमुना २ - लेखाधिकारी यांना पत्र",
    language="en",
    blocks=[
        ("heading", "Heading", "FORM 2", False),
        ("subheading", "Sub-heading",
         "Letter to the Accounts Officer forwarding the papers for payment of Gratuity of Government Servant", True),
        ("gov_block", "Government address block (top right)",
         "No.\nGovernment of Maharashtra\nDepartment of Education\nDate:", True),
        ("subject_label", "Subject label", "Subject : Authorisation of Gratuity in respect of", False),
        ("salutation", "Salutation", "Sir / Madam,", False),
        ("body", "Opening paragraph",
         "I am directed to forward herewith the papers for payment of Gratuity in respect of", True),
        ("body_2", "Opening paragraph continuation", "of this Department / Office", True),
        ("body_3", "Opening paragraph end", "for further necessary action.", True),
        ("point_2", "Point 2",
         "The details of Government dues which will remain outstanding on the date of death / Retirement of the Government servant and which need to be recovered / withheld are indicated in item No.12 of Form 1.", True),
        ("point_3", "Point 3", "The receipt of this letter may be acknowledged.", True),
        ("point_4", "Point 4",
         "The retirement / death gratuity will be drawn and disbursed by this Ministry / Department / Office on receipt of authority from you.", True),
        ("yours", "Sign-off", "Yours faithfully,", False),
        ("signatory", "Signatory caption", "(Head of Office)", False),
        ("enclosures_label", "Enclosures label", "Enclosures :", False),
        ("enclosure_1", "Enclosure 1",
         "Form 1 Completed, along with enclosures and checklists.", True),
        ("enclosure_2", "Enclosure 2",
         "Service Book (date of death / retirement to be indicated in the service book)", True),
        ("notes", "Closing note",
         "Notes : When initials or name of the Government Servant are or is incorrectly given in the various records consulted, this fact should be mentioned in the letter.", True),
    ],
)
def build_form_2(d: Doc):
    d.para("{{ t.heading }}", align="center", size=12, bold=True, space_after=4)
    d.para("{{ t.subheading }}", align="center", size=10, space_after=4)
    d.para("{{ t.gov_block }}", size=11, indent=8.5, space_after=10)
    d.para("To,", size=11)
    d.para("{{ office.ag_office_en }}", size=11, indent=1.2)
    d.para("-----------------------------------", size=11, indent=1.2, space_after=10)
    d.para("{{ t.subject_label }}", size=11, align="center")
    d.para("{{ emp.name_en }}, {{ emp.designation_en }}", size=11, bold=True,
           align="center", space_after=10)
    d.para("{{ t.salutation }}", size=11, space_after=8)
    d.para([("{{ t.body }} ", {}),
            ("{{ emp.name_en }}, {{ emp.designation_en }} ", {"bold": True}),
            ("{{ t.body_2 }} ", {}),
            ("{{ school.department_en }} Department ({{ school.name_en }}, "
             "Tal.{{ school.taluka_en }}, Dist.{{ school.district_en }}) ", {"bold": True}),
            ("{{ t.body_3 }}", {})],
           size=11, align="justify", first_line=1.2, line_spacing=1.5, space_after=8)
    for idx, key in ((2, "point_2"), (5, "point_3"), (6, "point_4")):
        d.para([(f"{idx}.   ", {}), ("{{ t." + key + " }}", {})],
               size=11, align="justify", indent=1.2, line_spacing=1.4, space_after=4)
    d.blank(2)
    d.para("{{ t.yours }}", size=11, align="right")
    d.blank(2)
    d.para("{{ t.signatory }}", size=11, align="right")
    d.blank(3)
    d.para("{{ t.enclosures_label }}", size=11)
    d.para("1.   {{ t.enclosure_1 }}", size=11, indent=1.0)
    d.para("2.   {{ t.enclosure_2 }}", size=11, indent=1.0, space_after=10)
    d.para("{{ t.notes }}", size=11, align="justify")


# ==========================================================================
# 5. Employee's own application (Marathi)
# ==========================================================================
@form(
    code="employee_application", order=5,
    title_en="Employee's application for sanction of DCRG",
    title_mr="कर्मचाऱ्याचा सेवानिवृत्ती उपदान प्रस्ताव अर्ज",
    language="mr",
    blocks=[
        ("to_label", "'To' label", "प्रति,", False),
        ("through_label", "'Through' label", "द्वारा-", False),
        ("subject", "Subject", "विषय- सेवानिवृत्ती उपदान (D.C.R.G) प्रस्ताव मंजुरी बाबत...", True),
        ("salutation", "Salutation", "सन्मानीय महोदय,", False),
        ("body", "Body - opening", "वरील विषयी विनंती की, मी दिनांक", True),
        ("body_2", "Body - continuation",
         "रोजी नियत वयोमानानुसार सेवानिवृत्त झालो आहे. माझे सेवानिवृत्ती उपदान (Gratuity) मंजूरी बाबतचा प्रस्ताव करणेसाठी विद्यालयाने वेळोवेळी आवश्यक त्या कागदपत्रांची मागणी केली तथापि मी वेळेत आवश्यक कागदपत्रे सादर करु शकलो नाही, त्यामुळे माझा सेवानिवृत्ती उपदान प्रस्ताव वेळेत सादर होवू शकला नाही. झालेल्या उशिरास पूर्णत: मी जबाबदार आहे. उशिराबाबत शासनाकडे मी कोणत्याही प्रकारची भरपाई वा व्याजाची मागणी करणार नाही.", True),
        ("closing", "Closing request",
         "तरी माझे सेवानिवृत्ती उपदान (Gratuity) मंजूर व्हावे, ही नम्र विनंती.", True),
        ("regards", "Sign-off", "कळावे.\nआपला विश्वासू,", True),
    ],
)
def build_employee_application(d: Doc):
    d.para("दिनांक: {{ letter_date }}", size=12, font=MR, indent=8.0)
    d.para("{{ emp.name_mr }}, {{ emp.designation_mr }}", size=12, font=MR, indent=8.0)
    d.para("{{ school.name_mr }}", size=12, font=MR, indent=8.0)
    d.para("ता.{{ school.taluka_mr }}, जि.{{ school.district_mr }}.",
           size=12, font=MR, indent=8.0, space_after=12)

    d.para("{{ t.to_label }}", size=12, font=MR)
    d.para("{{ office.addressee_mr }}", size=12, font=MR, indent=1.6, space_after=8)
    d.para("{{ t.through_label }}   मा.मुख्याध्यापक,", size=12, font=MR, indent=1.6)
    d.para("{{ school.name_mr }}", size=12, font=MR, indent=2.8)
    d.para("ता.{{ school.taluka_mr }}, जि.{{ school.district_mr }}.",
           size=12, font=MR, indent=2.8, space_after=10)
    d.para([("{{ t.subject }}", {"bold": True})], size=12, font=MR, indent=1.6,
           space_after=12)
    d.para("{{ t.salutation }}", size=12, font=MR, space_after=6)
    d.para([("{{ t.body }} ", {}),
            ("{{ emp.dor_f }} ", {"bold": True}),
            ("{{ t.body_2 }}", {})],
           size=12, font=MR, align="justify", first_line=1.4, line_spacing=1.9)
    d.para("{{ t.closing }}", size=12, font=MR, align="justify",
           first_line=1.4, line_spacing=1.9, space_after=10)
    d.para("{{ t.regards }}", size=12, font=MR, align="right")
    d.blank(3)
    d.para("({{ emp.name_mr }})", size=12, font=MR, indent=9.0)
    d.para("मोबा.नं.{{ emp.mobile }}", size=12, font=MR, indent=9.0)
    d.para("मु.-{{ emp.addr_at_mr }}, पोष्ट.-{{ emp.addr_post_mr }}", size=12, font=MR, indent=9.0)
    d.para("ता.{{ emp.addr_taluka_mr }}, जि.{{ emp.addr_district_mr }}", size=12, font=MR, indent=9.0)
    d.para("पिन-{{ emp.addr_pin }}", size=12, font=MR, indent=9.0)


# ==========================================================================
# 6. Employee & bank particulars
# ==========================================================================
@form(
    code="employee_bank_details", order=6,
    title_en="Employee and bank particulars",
    title_mr="कर्मचारी व बँक तपशील",
    language="both",
    blocks=[
        ("l_name", "Row 1 label", "सेवकाचे नांव", False),
        ("l_marathi", "Marathi sub-label", "मराठीत", False),
        ("l_english", "English sub-label", "इंग्रजीत", False),
        ("l_desig", "Designation label", "हुददा", False),
        ("l_dob", "Date of birth label", "जन्मतारीख", False),
        ("l_dor", "Retirement date label", "सेवानिवृत्ती दिनांक", False),
        ("l_mobile", "Mobile label", "मोबाईल नंबर", False),
        ("l_email", "Email label", "ई मेल आयडी", False),
        ("l_aadhaar", "Aadhaar label", "आधार नंबर", False),
        ("l_pan", "PAN label", "पॅन नंबर", False),
        ("l_bank", "Bank block label", "बँकेचा तपशील", False),
        ("l_bank_name", "Bank name label", "बँकेचे नांव", False),
        ("l_branch", "Branch label", "शाखेचे नांव", False),
        ("l_account", "Account number label", "बँक खाते क्रमांक", False),
        ("l_micr", "MICR label", "MICR CODE", False),
        ("l_ifsc", "IFSC label", "IFSC CODE", False),
        ("signatory", "Signatory caption", "मुख्याध्यापक", False),
    ],
)
def build_employee_bank_details(d: Doc):
    letterhead_mr(d, rule=False)
    d.blank()
    w = d.content_cm
    t = d.table([1.1, 5.0, 2.4, w - 8.5])
    tr = d.row(t, ["1.", "{{ t.l_name }}", "{{ t.l_marathi }}", "{{ emp.name_mr }}"],
               size=11, font=MR, bolds=[False, False, False, True])
    d.row(t, ["", "", "{{ t.l_english }}", "{{ emp.name_en_upper }}"],
          size=11, font=MR, bolds=[False, False, False, True])

    def r(num, label, value, bold=True):
        tr = d.row(t, [num, label, "", value], size=11, font=MR,
                   bolds=[False, False, False, bold])
        d.merge_row(tr, 1, 2)
        return tr

    r("2.", "{{ t.l_desig }}", "{{ emp.designation_en_upper }}")
    r("3.", "{{ t.l_dob }}", "{{ emp.dob_f }}")
    r("4.", "{{ t.l_dor }}", "{{ emp.dor_f }}")
    r("5.", "{{ t.l_mobile }}", "{{ emp.mobile }}")
    r("", "{{ t.l_email }}", "{{ emp.email }}")
    r("6.", "{{ t.l_aadhaar }}", "{{ emp.aadhaar|spaced }}")
    r("7", "{{ t.l_pan }}", "{{ emp.pan|spaced }}")
    r("8.", "{{ t.l_bank }}", "")

    for numeral, label, value in (
        ("i)", "{{ t.l_bank_name }}", "{{ bank.name }}"),
        ("ii)", "{{ t.l_branch }}", "{{ bank.branch_address }}"),
        ("iii)", "{{ t.l_account }}", "{{ bank.account_no|spaced }}"),
        ("iv)", "{{ t.l_micr }}", "{{ bank.micr|spaced }}"),
        ("v)", "{{ t.l_ifsc }}", "{{ bank.ifsc|spaced }}"),
    ):
        d.row(t, ["", f"{numeral}  {label}", "", value], size=11, font=MR,
              bolds=[False, False, False, True])

    d.blank(3)
    d.para("{{ t.signatory }}", size=11, font=MR, indent=2.0)


# ==========================================================================
# 7. Form I - Form for Assessing Gratuity (Part I)
# ==========================================================================
@form(
    code="form_1_assessing_gratuity", order=7, margin_cm=1.2,
    title_en="Form I - Form for Assessing Gratuity (Part I)",
    title_mr="नमुना १ - उपदान निश्चितीचा नमुना",
    language="en",
    blocks=[
        ("heading", "Heading", "FORM I", False),
        ("subheading", "Sub-heading", "Form for Assessing Gratuity", False),
        ("note_line", "Note under the heading",
         "[To be sent four months before the date of retirement to the PAO]", False),
        ("part_label", "Part label", "PART -I   (To be filled by Head of Office)", False),
        ("continued", "Page-2 marker", "... 2...", False),
        ("place_label", "Place label", "Place-", False),
        ("date_label", "Date label", "Date -", False),
        ("countersign", "Countersigned block",
         "Countersigned by:\nEducation Officer\nZilla Parishad, {{ school.district_en }}", True),
    ],
)
def build_form_1(d: Doc):
    d.para("{{ t.heading }}", align="center", size=11, bold=True)
    d.para("{{ t.subheading }}", align="center", size=11)
    d.para("{{ t.note_line }}", align="center", size=11)
    d.para("{{ t.part_label }}", align="center", size=11, space_after=2)

    w = d.content_cm
    t = d.table([1.2, w * 0.52, w - 1.2 - w * 0.52])

    def row(num, label, value, indent_label=False, bold=True, align="left"):
        d.row(t, [num, ("      " if indent_label else "") + label, value], size=8.5,
              bolds=[False, False, bold], aligns=["center", "left", align], valign="top")

    row("1.", "Name of the retiring Government Servant", "{{ emp.name_en_upper }}")
    row("2.", "Father's name (and also husband's name in the case of female Government servant)",
        "{{ emp.father_name_en }}")
    row("3.", "Mother's Name", "{{ emp.mother_name_en }}")
    row("4.", "Date of Birth", "{{ emp.dob_f }}")
    row("5.", "Permanent residential address showing village, town, district and State",
        "{{ emp.address_block }}\nSTATE- {{ emp.addr_state }}")
    row("6.", "PAN NO.", "{{ emp.pan|spaced }}")
    row("7.", "Post held at the time of retirement", "")
    row("", "a)   Name of the office", "{{ school.name_en }}", indent_label=True)
    row("", "b)   Post held", "{{ emp.designation_en_upper }}", indent_label=True)
    row("", "c)   Level of Pay in the Pay Matrix", "{{ pay.matrix_full }}", indent_label=True)
    row("", "d)   Basic Pay", "Rs.{{ pay.basic_r }}", indent_label=True)
    row("", "e)   Whether declared substantive in any post under the State Government",
        "{{ emp.substantive }}", indent_label=True)
    row("8.", "Date of Beginning of Service", "{{ emp.doj_combined }}")
    row("9.", "Date of Ending of Service", "{{ emp.dor_f }}")
    row("10.", "Cause of Ending of service (please tick one)", "")
    causes = [
        ("(a)", "Superannuation", "superannuation"),
        ("(b)", "On being declared surplus", "surplus"),
        ("(c)", "Voluntary / premature retirement at the initiative of the Government servant", "voluntary"),
        ("(d)", "Premature retirement at the initiative of the Government", "premature"),
        ("(e)", "Permanent absorption in Public Sector Undertaking/Autonomous Body", "absorption"),
        ("(f)", "Invalidment on Medical Ground", "invalid"),
        ("(g)", "Due to abolition of Post", "abolition"),
        ("(h)", "Compulsory retirement", "compulsory"),
        ("(i)", "Removal from Service", "removal"),
    ]
    for tag, label, key in causes:
        value = ("{% if meta.class_of_pension|lower == '" + key + "' %}"
                 "{{ meta.class_of_pension|upper }}{% else %}--{% endif %}")
        d.row(t, ["", f"      {tag}  {label}", value], size=8.5,
              bolds=[False, False, True], aligns=["center", "left", "center"], valign="top")

    tr = d.row(t, ["10.A", "In the case of compulsory retirement, the orders of the competent "
                           "authority whether Gratuity may be allowed at full rates or at reduced "
                           "rates and in case of reduced rates, the percentage at which it is to "
                           "be allowed.", ""], size=9, valign="top")
    d.merge_row(tr, 1, 2)
    tr = d.row(t, ["10.B", "In case of removal from service whether orders of competent authority "
                           "have been Obtained for grant of Gratuity and if so, at which rate", ""],
               size=9, valign="top")
    d.merge_row(tr, 1, 2)
    tr = d.row(t, ["11.", "Service in Autonomous body / State Government, if any", ""],
               size=9, valign="top")
    d.merge_row(tr, 1, 2)
    row("", "(a)  Details of Service", "", indent_label=True)
    row("", "Name of Organisation", "{{ school.name_en }}")
    row("", "Post held", "{{ emp.designation_en_upper }}")
    row("", "Period of Service",
        "From  {{ emp.doj_unaided_f }} To {{ svc.unaided_end_f }} (UN AIDED),\n"
        "From  {{ emp.doj_aided_f }} To {{ emp.dor_f }} (100% AIDED)")
    row("", "(b)  Whether the above service is to be counted for Gratuity in the Government",
        "YES", indent_label=True, align="center")
    row("", "(c)  Whether the Autonomous Organisation has discharged its gratuity Liability to "
            "the State Government", "Not Applicable", indent_label=True, align="center")

    d.para("...2", align="right", size=10)
    d.page_break()

    # ---------------- page 2 --------------------------------------------
    d.para("{{ t.continued }}", align="center", size=10, space_after=4)
    t2 = d.table([1.2, w * 0.52, w - 1.2 - w * 0.52])

    def row2(num, label, value, indent_label=False, align="center"):
        d.row(t2, [num, ("      " if indent_label else "") + label, value], size=8.5,
              bolds=[False, False, True], aligns=["center", "left", align], valign="top")

    row2("12.", "Whether any Department of Judicial Proceeding are pending against the retiring "
                "employee. (If yes, gratuity will be withheld till the conclusion of departmental "
                "of judicial proceeding and issue of final orders)",
         "{{ raw.service.dept_enquiry_pending }}")
    row2("13.", "Details of Service....", "")
    row2("", "(a) Period of Service",
         "From  {{ emp.doj_unaided_f }} To {{ svc.unaided_end_f }} (UN AIDED),\n"
         "From  {{ emp.doj_aided_f }} To {{ emp.dor_f }} (100% AIDED)", indent_label=True,
         align="left")
    row2("", "Total duration of Service", "{{ svc.net.dashed }} (100% aided Service)",
         indent_label=True)
    row2("", "(b) Details of omissions, imperfection or Deficiencies in the Service Book which "
             "have been ignored.", "No", indent_label=True)
    row2("", "(c) Period not counting as qualifying service", "No", indent_label=True)
    row2("", "(i)  Extraordinary Leave not counting as qualifying Service", "NIL", indent_label=True)
    row2("", "(ii)  Periods of suspension not treated as qualifying Service",
         "From   ---   to   ---", indent_label=True)
    row2("", "(iii) Interruptions in Service", "NIL", indent_label=True)
    row2("", "(iv) Periods of foreign service with United Nation Bodies for which no contribution "
             "for gratuity was received", "No", indent_label=True)
    row2("", "(v)  Any other period not treated as qualifying service  (Give Details)",
         "From   ---   to   ---", indent_label=True)
    row2("", "(d) Additions to qualifying service:", "NA", indent_label=True)
    row2("", "(i)  Benefit of service in an Autonomous Body", "NA", indent_label=True)
    row2("", "(e) Net Qualifying Service (a-b-c +d)",
         "{{ svc.net.y }} Y-{{ svc.net.mm }} M-{{ svc.net.dd }} D", indent_label=True)
    row2("", "(f) Qualifying Service expressed in terms of completed six monthly periods "
             "(Period of three months and above is to be treated as completed six monthly period",
         "{{ svc.periods_words }}", indent_label=True)
    row2("14.", "Last Pay", "Rs. {{ svc.last_pay_r }}")
    tr = d.row(t2, ["", "Note-If the Officer was foreign service immediately preceding retirement, "
                        "the Notional Last Pay which he would have drawn under Government but "
                        "being on foreign service may be mentioned.", ""], size=9, valign="top")
    d.merge_row(tr, 1, 2)
    row2("15.", "Amount of Retirement Gratuity / Death Gratuity", "Rs. {{ svc.dcrg_r }}")
    row2("16.", "Details of gratuity on finalisation of Department/Judicial proceedings", "")
    row2("", "(a) Percentage of gratuity after deduction of amount withheld",
         "{{ raw.service.withheld_pct }}", indent_label=True)
    row2("", "(b) Amount of gratuity after deduction of amount withheld",
         "Rs. {{ svc.dcrg_r }}", indent_label=True)
    row2("17.", "Details of Government dues recoverable out of gratuity", "")
    row2("", "(a) Licence fee for Govt. accommodation", "{{ raw.service.licence_fee }}",
         indent_label=True)
    row2("", "(b) Dues", "{{ raw.service.dues_recoverable }}", indent_label=True)
    row2("", "(c) Amount indicated by Executive Engineer to be withheld",
         "{{ raw.service.dues_recoverable }}", indent_label=True)
    row2("", "Post retirement address of the retiree", "{{ emp.address_inline }}", align="left")
    row2("", "E mail ID, if any", "{{ emp.email|blank }}")
    row2("", "Mobile No. if any", "{{ emp.mobile }}")

    d.para("{{ t.place_label }} {{ meta.place }}", size=10, space_before=4)
    d.para("{{ t.date_label }}  {{ letter_date }}", size=10)
    d.para("{{ t.countersign }}", size=10)


# ==========================================================================
# 8. Head of Office checklist + Form I account enfacement
# ==========================================================================
@form(
    code="checklist_and_enfacement", order=8, margin_cm=1.3,
    title_en="Check list for Head of Office + Form I (Account Enfacement)",
    title_mr="मुख्याध्यापक तपासणी सूची व नमुना १ (लेखा नोंद)",
    language="en",
    blocks=[
        ("heading", "Checklist heading",
         "CHECK LIST FOR HEAD OF OFFICE FOR TIMELY PROCESSING OF RETIREMETN DUES", False),
        ("heading2", "Second heading", "FORM I", False),
        ("subheading2", "Second sub-heading", "[Account Enfacement (by Accounts Officer)]", False),
        ("place_label", "Place label", "Place-", False),
        ("date_label", "Date label", "Date -", False),
        ("countersign", "Countersigned block",
         "Counter signed by\nEducation Officer\nZilla Parishad, {{ school.district_en }}", True),
        ("ao_signature", "Accounts Officer caption", "Signature of Accounts Officer", False),
    ],
)
def build_checklist(d: Doc):
    d.para("{{ t.heading }}", align="center", size=10, bold=True, space_after=2)
    w = d.content_cm
    t = d.table([1.0, w * 0.60, w - 1.0 - w * 0.60])

    items = [
        ("1.", "Whether retiring employee is an allottee of Government accommodation",
         "{{ chk.allottee_govt_accommodation }}"),
        ("2", "The date on receipt on which action initiated to obtain the 'No demand "
              "Certificate' from Executive Engineer", "Not Applicable"),
        ("3", "Date of receipt of 'No demand Certificate' from Executive Engineer", "Not Applicable"),
        ("4", "Date on which intimation regarding any recovery/withholding of amount from "
              "gratuity received from Executive Engineer", "Not Applicable"),
        ("5", "If retiring employee is not an allottee of Government accommodation, date on "
              "which 'No demand Certificate' issued by the office", "Not Applicable"),
        ("6", "Date on which action initiated to assess the service and emoluments qualifying "
              "for gratuity", "{{ chk.date_service_assessed|dt }}"),
        ("7", "Date on which action initiated to assess the Government dues other than the dues "
              "relating to allotment of Government accommodation", "{{ chk.date_dues_assessed|dt }}"),
        ("8", "Date on which the retiring Government Servant was furnished with a certificate "
              "regarding the length of qualifying service and the emoluments proposed to be "
              "reckoned for retirement gratuity",
         "{{ svc.net.y }} Y-{{ svc.net.mm }} M-{{ svc.net.dd }} D\n"
         "{{ chk.date_certificate_furnished|dt }}"),
        ("9", "Whether any objection received from the employee on the above certificate",
         "{{ chk.objection_received }}"),
        ("10", "Whether nominations made for", ""),
        ("", "        Death Gratuity  / Retirement Gratuity", "{{ chk.nomination_made }}"),
        ("11", "Whether Details of family attached", "{{ chk.family_details_attached }}"),
        ("12", "Whether the orders of the competent authority regarding Grant of gratuity in the "
               "cases of compulsory retirement/removal place on record", "Not Applicable"),
        ("13", "Whether order for withholding gratuity on finalisation of Departmental/judicial "
               "proceedings attached. if applicable on finalisation of proceedings", "Not Necessary"),
        ("14", "Whether statement indicating the reasons for delay (in case the papers for payment "
               "of gratuity are not forwarded before four months of the retirement of Government "
               "servant) attached", "{{ chk.delay_reason_gr }}"),
        ("15", "Whether brief statement leading to reinstatement of the Government servant attached "
               "(in case the Government Servant has been reinstated after having been suspended "
               "Compulsorily retired from service", "---"),
    ]
    for num, label, value in items:
        d.row(t, [num, label, value], size=8, bolds=[False, False, True],
              aligns=["center", "left", "left"], valign="top")

    d.blank()
    d.para("{{ t.heading2 }}", align="center", size=11, bold=True)
    d.para("{{ t.subheading2 }}", align="center", size=10, space_after=3)

    t2 = d.table([1.2, w * 0.58, w - 1.2 - w * 0.58])
    tr = d.row(t2, ["", "Date of receipt of papers for payment of gratuity by the Accounts Officer "
                        "From Head of Officer", "{{ chk.ag_receipt_date|dt }}"],
               size=8, bolds=[False, False, True], valign="top")
    d.merge_row(tr, 0, 1)
    tr = d.row(t2, ["", "Entitlements admitted-", ""], size=8, bold=True, valign="top")
    d.merge_row(tr, 0, 2)

    ent = [
        ("A.", "Length of qualifying service", "{{ svc.net.words_en }}"),
        ("B.", "Retirement / Death Gratuity", "{{ meta.class_of_pension }}"),
        ("(i)", "Total amount of gratuity", "Rs. {{ svc.dcrg_r }}"),
        ("(ii)", "Percentage of gratuity to be withheld", "---"),
        ("(iii)", "Amount of gratuity after deduction of amount withheld", "Rs. {{ svc.dcrg_r }}"),
        ("(iv)", "Amount to be adjusted towards arrears of licence fee for Government "
                 "accommodation beyond retirement", "Nil"),
        ("(v)", "Amount intimated by Executive Engineer for being withheld on account of "
                "un assessed licence fee", "Nil"),
        ("(vi)", "Amount to be adjusted towards Government dues other than those Pertaining to "
                 "Government accommodation", "Nil"),
        ("(vii)", "Net amount to be released immediately", "Rs. {{ svc.dcrg_r }}"),
        ("C.", "Head of account to which the amount of retirement /death gratuity to be debited", ""),
        ("D.", "Whether any order affecting gratuity issued", "No."),
        ("", "        If so, details thereof", "---"),
    ]
    for tag, label, value in ent:
        d.row(t2, [tag, label, value], size=8, bolds=[False, False, True],
              aligns=["center", "left", "left"], valign="top")

    d.para("{{ t.place_label }}{{ meta.place }}", size=10, space_before=4)
    d.para("{{ t.date_label }} {{ letter_date }}", size=10)
    d.two_col("{{ t.countersign }}", "{{ t.ao_signature }}", size=10, right_align="left")


# ==========================================================================
# 9. Marathi certificate - 100% aided post
# ==========================================================================
@form(
    code="certificate_aided_post", order=9,
    title_en="Certificate - retired from a 100% aided post",
    title_mr="प्रमाणपत्र - १००% अनुदानित पदावरून सेवानिवृत्त",
    language="mr",
    blocks=[
        ("heading", "Heading", "प्रमाणपत्र", False),
        ("intro", "Opening line", "प्रमाणित करण्यात येते की,-", False),
        ("school_label", "School label", "शाळेचे नांव-", False),
        ("body", "Body - opening", "हे कर्मचारी हे दिनांक", True),
        ("body_2", "Body - continuation", "रोजी नियुक्त झालेले असून, ते", True),
        ("body_3", "Body - end",
         "पासून 100 टक्के अनुदानावर आहेत. तसेच ते 100 टक्के अनुदानित पदावरुन सेवानिवृत्त झाले आहेत.", True),
        ("responsibility", "Responsibility statement",
         "याबाबत काही चुकीचे आढळल्यास त्याची सर्वस्वी जबाबदारी मुख्याध्यापक म्हणून माझी राहीन.", True),
        ("place_label", "Place label", "स्थळ-", False),
        ("date_label", "Date label", "दिनांक-", False),
        ("signatory", "Signatory caption", "मुख्याध्यापक", False),
    ],
)
def build_certificate_aided(d: Doc):
    d.para("{{ t.heading }}", align="center", size=15, bold=True, font=MR, space_after=12)
    d.para("{{ t.intro }}", size=13, font=MR, first_line=1.6, space_after=6)
    d.para([("{{ emp.name_mr }}", {"bold": True}),
            (", पदनाम-", {}),
            ("{{ emp.designation_mr }}", {"bold": True})],
           size=13, font=MR, line_spacing=1.6)
    d.para([("{{ t.school_label }} ", {}),
            ("{{ school.name_mr }}", {"bold": True})], size=13, font=MR, line_spacing=1.6)
    d.para([("ता.{{ school.taluka_mr }}, जि.{{ school.district_mr }}.", {"bold": True})],
           size=13, font=MR, indent=1.6, line_spacing=1.6, space_after=6)
    d.para([("{{ t.body }} ", {}),
            ("{{ emp.doj_unaided_f }} ", {"bold": True}),
            ("{{ t.body_2 }} ", {}),
            ("{{ emp.doj_aided_f }} ", {"bold": True}),
            ("{{ t.body_3 }}", {})],
           size=13, font=MR, align="justify", first_line=1.6, line_spacing=1.7)
    d.para("{{ t.responsibility }}", size=13, font=MR, align="justify",
           first_line=1.6, line_spacing=1.7, space_after=16)
    d.two_col("{{ t.place_label }} {{ meta.place_mr }}\n{{ t.date_label }}{{ letter_date }}",
              "{{ t.signatory }}", size=12, font=MR, right_align="center")
