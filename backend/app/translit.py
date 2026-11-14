# -*- coding: utf-8 -*-
"""Transliteration between Devanagari and Latin script.

These forms carry the same name in both scripts, so one is typed and the other
transliterated. The two directions are not equally reliable:

*   **Devanagari to Latin is dependable.** Devanagari spells what is spoken, so
    the mapping is nearly one-way-deterministic. The only judgement call is
    schwa deletion -- कडलग is written "Kadlag", not "Kadlaga" -- which is
    handled below.

*   **Latin to Devanagari is a guess.** English spelling does not record vowel
    length or which of the two "t"/"d"/"n" families is meant, so "Kadlag" could
    be कडलग or कडलाग, and "Patil" पाटील or पटिल. It is offered as a starting
    point that must be checked, never as an authority.

So the intended workflow is: type the Marathi, generate the English, correct it.

Words that are translated rather than transliterated -- a designation such as
शिपाई is "Peon", not "Shipai" -- come from GLOSSARY first.
"""
from __future__ import annotations

import re

# --------------------------------------------------------------------------
# Terms that translate rather than transliterate.
# --------------------------------------------------------------------------
GLOSSARY: dict[str, str] = {
    "शिपाई": "Peon",
    "पूर्णवेळ शिपाई": "Full Time Peon",
    "पुर्णवेळ शिपाई": "Full Time Peon",
    "शिक्षक": "Teacher",
    "सहाय्यक शिक्षक": "Assistant Teacher",
    "सहायक शिक्षक": "Assistant Teacher",
    "मुख्याध्यापक": "Head Master",
    "उपमुख्याध्यापक": "Deputy Head Master",
    "पर्यवेक्षक": "Supervisor",
    "लिपिक": "Clerk",
    "वरिष्ठ लिपिक": "Senior Clerk",
    "कनिष्ठ लिपिक": "Junior Clerk",
    "ग्रंथपाल": "Librarian",
    "प्रयोगशाळा सहाय्यक": "Laboratory Assistant",
    "चौकीदार": "Watchman",
    "सफाई कामगार": "Sweeper",
    "शिक्षणाधिकारी": "Education Officer",
    "जिल्हा परिषद": "Zilla Parishad",
    "विद्यालय": "Vidyalaya",
    "प्रशाला": "Prashala",
    "पुरुष": "Male",
    "स्त्री": "Female",
}

REVERSE_GLOSSARY = {v.lower(): k for k, v in GLOSSARY.items()}

# --------------------------------------------------------------------------
# Devanagari -> Latin
# --------------------------------------------------------------------------
_VOWELS = {
    "अ": "a", "आ": "a", "इ": "i", "ई": "i", "उ": "u", "ऊ": "u",
    "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au", "ऋ": "ru", "ॠ": "ru",
    "ऍ": "ae", "ऑ": "o", "अं": "an", "अः": "ah",
}

_MATRAS = {
    "ा": "a", "ि": "i", "ी": "i", "ु": "u", "ू": "u", "े": "e",
    "ै": "ai", "ो": "o", "ौ": "au", "ृ": "ru", "ॅ": "ae", "ॉ": "o",
}

_CONSONANTS = {
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "n",
    "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "n",
    "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n",
    "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m",
    "य": "y", "र": "r", "ल": "l", "ळ": "l", "व": "v",
    "श": "sh", "ष": "sh", "स": "s", "ह": "h",
    "क्ष": "ksh", "ज्ञ": "dny", "त्र": "tr", "श्र": "shr",
    "ड़": "d", "ढ़": "dh", "फ़": "f", "ज़": "z", "क़": "q", "ग़": "gh",
}

_VIRAMA = "्"
_ANUSVARA = "ं"
_CHANDRABINDU = "ँ"
_VISARGA = "ः"
_NUKTA = "़"
_DEV_DIGITS = {d: str(i) for i, d in enumerate("०१२३४५६७८९")}

_DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")


def has_devanagari(text: str) -> bool:
    return bool(_DEVANAGARI_RE.search(text or ""))


def _syllables(word: str) -> list[tuple[str, bool]]:
    """Break a Devanagari word into (latin, carries_inherent_a) pieces.

    Whether the vowel is inherent matters, because only an inherent 'a' may be
    dropped: राहाता is written with explicit matras and stays "Rahata", while
    कडलग is all inherent and loses its last vowel.
    """
    out: list[tuple[str, bool]] = []
    i = 0
    n = len(word)
    while i < n:
        ch = word[i]

        # Two-character conjuncts spelled as a unit.
        pair = word[i:i + 3]
        matched = next((c for c in ("क्ष", "ज्ञ", "त्र", "श्र") if pair.startswith(c)), None)
        if matched:
            i += len(matched)
            out.append(_with_vowel(_CONSONANTS[matched], word, i))
            i = _skip_vowel_signs(word, i)
            continue

        if ch in _DEV_DIGITS:
            out.append((_DEV_DIGITS[ch], False)); i += 1; continue

        if ch in _VOWELS:
            out.append((_VOWELS[ch], False)); i += 1
            i = _skip_marks(word, i, out)
            continue

        if ch in _CONSONANTS:
            i += 1
            if i < n and word[i] == _NUKTA:
                i += 1
            out.append(_with_vowel(_CONSONANTS[ch], word, i))
            i = _skip_vowel_signs(word, i)
            continue

        if ch in (_ANUSVARA, _CHANDRABINDU):
            out.append(("n", False)); i += 1; continue
        if ch == _VISARGA:
            out.append(("h", False)); i += 1; continue
        if ch == _VIRAMA:
            i += 1; continue

        out.append((ch, False)); i += 1
    return out


def _with_vowel(consonant: str, word: str, index: int) -> tuple[str, bool]:
    """Attach the following matra, or the inherent 'a' when there is none."""
    if index < len(word):
        nxt = word[index]
        if nxt in _MATRAS:
            return consonant + _MATRAS[nxt], False
        if nxt == _VIRAMA:
            return consonant, False
    return consonant + "a", True


def _skip_vowel_signs(word: str, index: int) -> int:
    while index < len(word) and word[index] in _MATRAS:
        index += 1
    if index < len(word) and word[index] == _VIRAMA:
        index += 1
    return index


def _skip_marks(word: str, index: int, out: list) -> int:
    while index < len(word) and word[index] in (_ANUSVARA, _CHANDRABINDU, _VISARGA):
        out.append(("n" if word[index] != _VISARGA else "h", False))
        index += 1
    return index


def _delete_schwa(syllables: list[tuple[str, bool]]) -> list[str]:
    """Drop the inherent vowels a reader would not pronounce.

    Two rules cover most names:

      * the final inherent 'a' goes -- कडलग is written "Kadlag", not "Kadlaga";
      * a medial inherent 'a' goes when the next syllable has a written vowel --
        रंगनाथ is "Rangnath" and सादतपूर is "Sadatpur".

    Anything beyond that needs a pronunciation lexicon, so some names still come
    out over-spelled (होळकर as "Holakar" rather than the usual "Holkar"). The
    output is a draft for the operator to correct, not an authority.
    """
    out = []
    last = len(syllables) - 1
    for index, (text, inherent) in enumerate(syllables):
        drop = False
        if inherent and len(text) > 1:
            if index == last and index > 0:
                drop = True
            elif 0 < index < last and not syllables[index + 1][1]:
                drop = True
        out.append(text[:-1] if drop else text)
    return out


def devanagari_to_latin(text: str, *, title_case: bool = True) -> str:
    """Transliterate Devanagari to Latin, dropping the final inherent vowel.

    Marathi names are written in English without the trailing 'a' of the last
    syllable: कडलग is "Kadlag", रंगनाथ is "Rangnath".
    """
    if not text:
        return ""
    if text.strip() in GLOSSARY:
        return GLOSSARY[text.strip()]

    pieces = []
    for token in re.split(r"(\s+|[.,;:/()\-–—])", text):
        if not token or not has_devanagari(token):
            pieces.append(token)
            continue
        if token in GLOSSARY:
            pieces.append(GLOSSARY[token])
            continue
        word = "".join(_delete_schwa(_syllables(token)))
        pieces.append(word.capitalize() if title_case and word else word)
    return "".join(pieces)


# --------------------------------------------------------------------------
# Latin -> Devanagari (approximate)
# --------------------------------------------------------------------------
# Longest-match first; English spelling is ambiguous, so this is a draft only.
_LATIN_CLUSTERS: list[tuple[str, str]] = [
    ("chh", "छ"), ("shr", "श्र"), ("ksh", "क्ष"), ("dny", "ज्ञ"), ("gny", "ज्ञ"),
    ("aai", "आई"), ("aa", "आ"), ("ee", "ी"), ("oo", "ू"), ("ai", "ै"), ("au", "ौ"),
    ("kh", "ख"), ("gh", "घ"), ("ch", "च"), ("jh", "झ"), ("th", "थ"), ("dh", "ध"),
    ("ph", "फ"), ("bh", "भ"), ("sh", "श"), ("tr", "त्र"),
    ("k", "क"), ("g", "ग"), ("j", "ज"), ("t", "त"), ("d", "द"), ("n", "न"),
    ("p", "प"), ("f", "फ"), ("b", "ब"), ("m", "म"), ("y", "य"), ("r", "र"),
    ("l", "ल"), ("v", "व"), ("w", "व"), ("s", "स"), ("h", "ह"), ("z", "झ"),
    ("c", "क"), ("q", "क"), ("x", "क्स"),
    ("a", "अ"), ("i", "इ"), ("u", "उ"), ("e", "ए"), ("o", "ओ"),
]

# Stops: a nasal before one of these is written as anusvara.
_STOPS = set("kgcjtdpbq")

_INDEPENDENT = {"अ": "", "आ": "ा", "इ": "ि", "ई": "ी", "उ": "ु", "ऊ": "ू",
                "ए": "े", "ऐ": "ै", "ओ": "ो", "औ": "ौ"}


def latin_to_devanagari(text: str) -> str:
    """Best-effort Latin to Devanagari. Always needs checking by a reader."""
    if not text:
        return ""
    key = text.strip().lower()
    if key in REVERSE_GLOSSARY:
        return REVERSE_GLOSSARY[key]

    pieces = []
    for token in re.split(r"(\s+|[.,;:/()\-–—])", text):
        if not token or not token.strip() or not re.search(r"[A-Za-z]", token):
            pieces.append(token)
            continue
        if token.strip().lower() in REVERSE_GLOSSARY:
            pieces.append(REVERSE_GLOSSARY[token.strip().lower()])
            continue
        pieces.append(_latin_word(token.lower()))
    return "".join(pieces)


def _latin_word(word: str) -> str:
    out = ""
    i = 0
    after_consonant = False
    while i < len(word):
        # A nasal closing a syllable is written as anusvara only before a stop:
        # Rangnath is रंगनाथ, but the "m" of Sangamner stays a letter -- संगमनेर.
        if (word[i] in "nm" and not after_consonant and out
                and i + 1 < len(word) and word[i + 1] in _STOPS):
            out += _ANUSVARA
            i += 1
            continue
        for latin, dev in _LATIN_CLUSTERS:
            if word.startswith(latin, i):
                is_vowel = latin[0] in "aeiou"
                if is_vowel:
                    # After a consonant a vowel becomes a matra, not a letter.
                    out += _INDEPENDENT.get(dev, dev) if after_consonant else dev
                    after_consonant = False
                else:
                    # No virama between consonants: Marathi writes कडलग, not
                    # कड्लग -- the unwritten inherent vowel does that work.
                    out += dev
                    after_consonant = True
                i += len(latin)
                break
        else:
            out += word[i]
            i += 1
            after_consonant = False
    return out


def convert(text: str, direction: str = "auto") -> dict:
    """Convert in the requested direction; 'auto' picks it from the script used."""
    text = text or ""
    if direction == "auto":
        direction = "mr2en" if has_devanagari(text) else "en2mr"
    if direction == "mr2en":
        return {"text": devanagari_to_latin(text), "direction": direction,
                "reliable": True}
    return {"text": latin_to_devanagari(text), "direction": "en2mr",
            "reliable": False}
