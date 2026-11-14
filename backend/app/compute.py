"""Date arithmetic, service-length and gratuity computation, and formatting.

Service length follows the usual government convention: a period stated as
"from A to B" is inclusive of B, so the duration is measured from A to B+1 day.
Verified against the reference case (01-03-2008 to 31-03-2024 = 16 Y 01 M 00 D).
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Iterable

from num2words import num2words

DCRG_MAX_PERIODS = 66            # qualifying service capped at 33 years
DCRG_CEILING = 2_000_000         # statutory ceiling on retirement gratuity

_DEV_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")

MR_MONTHS = ["जानेवारी", "फेब्रुवारी", "मार्च", "एप्रिल", "मे", "जून",
             "जुलै", "ऑगस्ट", "सप्टेंबर", "ऑक्टोबर", "नोव्हेंबर", "डिसेंबर"]
EN_MONTHS = ["January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"]


# --------------------------------------------------------------------------
# parsing / formatting
# --------------------------------------------------------------------------
def parse_date(value) -> date | None:
    """Accept date, ISO (yyyy-mm-dd) or Indian (dd-mm-yyyy / dd/mm/yyyy) text."""
    if value in (None, "", "--", "---"):
        return None
    if isinstance(value, date):
        return value
    s = str(value).strip()
    m = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$", s)
    if m:
        y, mo, d = (int(x) for x in m.groups())
        return date(y, mo, d)
    m = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$", s)
    if m:
        d, mo, y = (int(x) for x in m.groups())
        return date(y, mo, d)
    return None


def fmt_date(value, empty: str = "") -> str:
    """dd-mm-yyyy, the format used throughout the printed case."""
    d = parse_date(value)
    return d.strftime("%d-%m-%Y") if d else empty


def fmt_date_long_en(value, empty: str = "") -> str:
    d = parse_date(value)
    return f"{d.day} {EN_MONTHS[d.month - 1]}, {d.year}" if d else empty


def fmt_date_mr(value, empty: str = "") -> str:
    """Marathi long date, e.g. 28 August, 2026 in Devanagari."""
    d = parse_date(value)
    if not d:
        return empty
    return f"{to_dev(d.day)} {MR_MONTHS[d.month - 1]}, {to_dev(d.year)}"


def fmt_date_dev(value, empty: str = "") -> str:
    """dd-mm-yyyy in Devanagari digits."""
    return to_dev(fmt_date(value, empty))


def to_dev(value) -> str:
    """Latin digits -> Devanagari digits."""
    return str(value).translate(_DEV_DIGITS)


def ordinal_en(n) -> str:
    try:
        n = int(n)
    except (TypeError, ValueError):
        return str(n)
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


# --------------------------------------------------------------------------
# money
# --------------------------------------------------------------------------
def indian_number(n) -> str:
    """1234567 -> '12,34,567' (Indian digit grouping)."""
    try:
        n = int(round(float(n)))
    except (TypeError, ValueError):
        return ""
    sign, s = ("-" if n < 0 else ""), str(abs(n))
    if len(s) <= 3:
        return sign + s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return sign + ",".join(parts + [tail])


def rupees(n, empty: str = "---") -> str:
    """'2,25,600/-' style used on the forms."""
    if n in (None, ""):
        return empty
    return f"{indian_number(n)}/-"


def amount_words_en(n) -> str:
    try:
        n = int(round(float(n)))
    except (TypeError, ValueError):
        return ""
    return num2words(n, lang="en_IN").replace(",", "").title() + " Only"


_MR_ONES = ["", "एक", "दोन", "तीन", "चार", "पाच", "सहा", "सात", "आठ", "नऊ"]
_MR_UNITS = [(10_000_000, "कोटी"), (100_000, "लाख"), (1_000, "हजार")]

# 0-99 in Marathi words.
_MR_TENS = {
    0: "", 1: "एक", 2: "दोन", 3: "तीन", 4: "चार", 5: "पाच",
    6: "सहा", 7: "सात", 8: "आठ", 9: "नऊ", 10: "दहा",
    11: "अकरा", 12: "बारा", 13: "तेरा", 14: "चौदा", 15: "पंधरा",
    16: "सोळा", 17: "सतरा", 18: "अठरा", 19: "एकोणीस", 20: "वीस",
    21: "एकवीस", 22: "बावीस", 23: "तेवीस", 24: "चोवीस", 25: "पंचवीस",
    26: "सव्वीस", 27: "सत्तावीस", 28: "अठ्ठावीस", 29: "एकोणतीस", 30: "तीस",
    31: "एकतीस", 32: "बत्तीस", 33: "तेहतीस", 34: "चौतीस", 35: "पस्तीस",
    36: "छत्तीस", 37: "सदतीस", 38: "अडतीस", 39: "एकोणचाळीस", 40: "चाळीस",
    41: "एक्केचाळीस", 42: "बेचाळीस", 43: "त्रेचाळीस", 44: "चव्वेचाळीस",
    45: "पंचेचाळीस", 46: "सेहेचाळीस", 47: "सत्तेचाळीस", 48: "अठ्ठेचाळीस",
    49: "एकोणपन्नास", 50: "पन्नास", 51: "एक्कावन्न", 52: "बावन्न",
    53: "त्रेपन्न", 54: "चोपन्न", 55: "पंचावन्न", 56: "छप्पन्न",
    57: "सत्तावन्न", 58: "अठ्ठावन्न", 59: "एकोणसाठ", 60: "साठ",
    61: "एकसष्ट", 62: "बासष्ट", 63: "त्रेसष्ट", 64: "चौसष्ट", 65: "पासष्ट",
    66: "सहासष्ट", 67: "सदुसष्ट", 68: "अडुसष्ट", 69: "एकोणसत्तर", 70: "सत्तर",
    71: "एकाहत्तर", 72: "बाहत्तर", 73: "त्र्याहत्तर", 74: "चौर्याहत्तर",
    75: "पंच्याहत्तर", 76: "शहात्तर", 77: "सत्त्याहत्तर", 78: "अठ्ठ्याहत्तर",
    79: "एकोणऐंशी", 80: "ऐंशी", 81: "एक्याऐंशी", 82: "ब्याऐंशी",
    83: "त्र्याऐंशी", 84: "चौऱ्याऐंशी", 85: "पंच्याऐंशी", 86: "शहाऐंशी",
    87: "सत्त्याऐंशी", 88: "अठ्ठ्याऐंशी", 89: "एकोणनव्वद", 90: "नव्वद",
    91: "एक्याण्णव", 92: "ब्याण्णव", 93: "त्र्याण्णव", 94: "चौऱ्याण्णव",
    95: "पंच्याण्णव", 96: "शहाण्णव", 97: "सत्त्याण्णव", 98: "अठ्ठ्याण्णव",
    99: "नव्व्याण्णव",
}


def _mr_below_thousand(n: int) -> str:
    if n <= 99:
        return _MR_TENS.get(n, str(n))
    hundreds, rest = divmod(n, 100)
    out = f"{_MR_ONES[hundreds]}शे"          # 'she' = hundred
    return f"{out} {_MR_TENS[rest]}".strip() if rest else out


def amount_words_mr(n) -> str:
    """Marathi amount in words, built on the Indian unit scale."""
    try:
        n = int(round(float(n)))
    except (TypeError, ValueError):
        return ""
    if n == 0:
        return "शून्य रुपये फक्त"
    parts: list[str] = []
    for value, name in _MR_UNITS:
        if n >= value:
            count, n = divmod(n, value)
            parts.append(f"{_mr_below_thousand(count)} {name}")
    if n:
        parts.append(_mr_below_thousand(n))
    return " ".join(parts) + " रुपये फक्त"


# --------------------------------------------------------------------------
# service duration
# --------------------------------------------------------------------------
class Duration:
    """A Y/M/D service duration, using 30-day months when normalising sums."""

    __slots__ = ("y", "m", "d")

    def __init__(self, y: int = 0, m: int = 0, d: int = 0):
        self.y, self.m, self.d = int(y), int(m), int(d)

    def __add__(self, other: "Duration") -> "Duration":
        return Duration(self.y + other.y, self.m + other.m, self.d + other.d).normalised()

    def __sub__(self, other: "Duration") -> "Duration":
        total = max(self.total_days() - other.total_days(), 0)
        return Duration(total // 360, (total % 360) // 30, total % 30)

    def normalised(self) -> "Duration":
        d, m, y = self.d, self.m, self.y
        m, d = m + d // 30, d % 30
        y, m = y + m // 12, m % 12
        return Duration(y, m, d)

    def total_days(self) -> int:
        return self.y * 360 + self.m * 30 + self.d

    def total_months(self) -> int:
        return self.y * 12 + self.m

    @property
    def dashed(self) -> str:
        """'16-01-00' -- the form's compact Y-M-D notation."""
        return f"{self.y:02d}-{self.m:02d}-{self.d:02d}"

    @property
    def words_en(self) -> str:
        return f"{self.y:02d} Years {self.m:02d} Months {self.d:02d} Days"

    @property
    def words_mr(self) -> str:
        return (f"{to_dev(f'{self.y:02d}')} वर्षे "
                f"{to_dev(f'{self.m:02d}')} महिने "
                f"{to_dev(f'{self.d:02d}')} दिवस")

    @property
    def is_zero(self) -> bool:
        return not (self.y or self.m or self.d)

    def as_dict(self) -> dict:
        # dyy/dmm/ddd print "--" for an entirely zero period, the way the
        # printed forms show a nil non-qualifying service or weightage.
        dash = "--"
        return {"y": self.y, "m": self.m, "d": self.d,
                "yy": f"{self.y:02d}", "mm": f"{self.m:02d}", "dd": f"{self.d:02d}",
                "dyy": dash if self.is_zero else f"{self.y:02d}",
                "dmm": dash if self.is_zero else f"{self.m:02d}",
                "ddd": dash if self.is_zero else f"{self.d:02d}",
                "zero": self.is_zero,
                "dashed": self.dashed, "words_en": self.words_en,
                "words_mr": self.words_mr}

    def __repr__(self) -> str:
        return f"Duration({self.dashed})"


def duration_between(start, end, inclusive: bool = True) -> Duration:
    """Y/M/D from *start* to *end*; ``inclusive`` counts the end date as served."""
    a, b = parse_date(start), parse_date(end)
    if not a or not b:
        return Duration()
    if inclusive:
        b = b + timedelta(days=1)
    if b < a:
        return Duration()
    y = b.year - a.year
    m = b.month - a.month
    d = b.day - a.day
    if d < 0:
        m -= 1
        prev_month_end = b.replace(day=1) - timedelta(days=1)
        d += prev_month_end.day
    if m < 0:
        y -= 1
        m += 12
    return Duration(y, m, d)


def sum_durations(items: Iterable[Duration]) -> Duration:
    total = Duration()
    for item in items:
        total = total + item
    return total


def six_monthly_periods(dur: Duration) -> int:
    """Completed six-monthly periods; a remainder of 3 months or more counts as one.

    Capped at 66 (33 years), per the retirement gratuity rules.
    """
    months = dur.total_months()
    periods, remainder = divmod(months, 6)
    if remainder >= 3 or (remainder == 2 and dur.d >= 15):
        periods += 1
    return min(periods, DCRG_MAX_PERIODS)


def retirement_gratuity(last_pay, periods: int) -> int:
    """Last pay / 4 x completed six-monthly periods, subject to the ceiling."""
    try:
        pay = float(last_pay)
    except (TypeError, ValueError):
        return 0
    return int(min(round(pay / 4 * periods), DCRG_CEILING))


def age_on(dob, on=None):
    """Age in completed years on a reference date (defaults to today)."""
    d = parse_date(dob)
    ref = parse_date(on) or date.today()
    if not d:
        return ""
    return ref.year - d.year - ((ref.month, ref.day) < (d.month, d.day))
