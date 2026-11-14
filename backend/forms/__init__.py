"""Registry of every form template in a DCRG case, in printing order."""
from . import forms_a, forms_b, forms_c

ALL_FORMS = forms_a.FORMS + forms_b.FORMS + forms_c.FORMS
ALL_FORMS.sort(key=lambda f: f["order"])

BY_CODE = {f["code"]: f for f in ALL_FORMS}
