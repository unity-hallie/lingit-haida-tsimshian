"""
Verb form guesses based on paradigm patterns.

We know the predictable parts of Tlingit verb morphology:
- Conjugation prefix per class × mode
- Subject prefix by person
- Classifier allomorph by mode

We do NOT know: stem variant per mode (unpredictable, must come from speakers).

A guess looks like: [conj_prefix] + [subject_prefix] + [classifier] + .ROOT[?]
Marked clearly as AI guess, unverified. Speaker confirms or corrects.

Paradigm data from: The Conjugator (X̱ʼunei Lance Twitchell), extracted from
Haa Wsineix̲ (Nora Marks Dauenhauer & Richard Dauenhauer).
"""

from __future__ import annotations

# ── Conjugation prefix by class × mode ────────────────────────────────────────
# Source: Crippen "Basics of Tlingit Verbal Structure"; Twitchell Conjugator
# Format: {conjugation_class: {mode_key: prefix_string}}
# "∅" means zero prefix (nothing appears)
# "wu-" means the perfective wu- prefix
# "u-" means the negative/potential prefix

CONJ_PREFIX: dict[str, dict[str, str]] = {
    "ø": {
        "imperfective":  "∅",
        "perfective":    "wu-",
        "habitual":      "∅",
        "potential":     "g̲-/k-",
        "imperative":    "∅",
        "prohibitive":   "u-",
    },
    "na": {
        "imperfective":  "na-",
        "perfective":    "wu-",
        "habitual":      "na-",
        "potential":     "na-g̲-",
        "imperative":    "na-",
        "prohibitive":   "na-u-",
    },
    "ga": {
        "imperfective":  "ga-",
        "perfective":    "wu-",
        "habitual":      "ga-",
        "potential":     "ga-g̲-",
        "imperative":    "ga-",
        "prohibitive":   "ga-u-",
    },
    "yi": {
        "imperfective":  "yi-",
        "perfective":    "wu-",
        "habitual":      "yi-",
        "potential":     "yi-g̲-",
        "imperative":    "yi-",
        "prohibitive":   "yi-u-",
    },
}

# ── Subject prefixes ───────────────────────────────────────────────────────────
# These appear AFTER the conjugation prefix, BEFORE the classifier
SUBJECT_PREFIX: dict[str, str] = {
    "1sg":  "x̱a-",   # I
    "2sg":  "i-",    # you (singular)
    "3":    "∅-",    # she/he/it/they
    "1pl":  "tu-",   # we
    "2pl":  "yi-",   # you all
    "4h":   "du-",   # someone (4th person human)
}

# ── Classifier allomorphs by mode ─────────────────────────────────────────────
# Most classifiers appear consistently; main change is –i/+i (incomplete/complete)
# For simplicity: imperfective/habitual/imperative = incomplete (–i)
#                 perfective/potential = complete (+i) for state verbs
COMPLETE_MODES = {"perfective", "potential"}


def make_guess(
    root: str,
    conjugation_class: str,
    classifier: str,
    mode: str,
) -> str | None:
    """
    Generate a guess for a verb form.

    Returns a string like "[na-][x̱a-][∅].ROOT[?]" showing the predictable
    prefix structure with stem marked as unknown.

    Returns None if we can't make a meaningful guess.
    """
    class_key = conjugation_class.lower().strip()
    mode_key = mode.lower().strip()

    if class_key not in CONJ_PREFIX:
        return None

    conj = CONJ_PREFIX[class_key].get(mode_key)
    if conj is None:
        return None

    # Build the prefix chain
    parts = []
    if conj != "∅":
        parts.append(conj)

    # Add placeholder for subject (shown as slot)
    parts.append("[S]")

    # Classifier
    cls = classifier if classifier else "∅"
    parts.append(f"{cls}-")

    # Stem with uncertainty marker
    parts.append(f"√{root}[?]")

    return "".join(parts)


def make_all_guesses(
    root: str,
    conjugation_class: str,
    classifier: str,
) -> dict[str, dict[str, str]]:
    """
    Generate guesses for all modes × subjects.

    Returns: {mode: {subject: guess_string}}
    """
    modes = ["imperfective", "perfective", "habitual", "potential", "imperative", "prohibitive"]
    result = {}
    for mode in modes:
        mode_guesses = {}
        for subj_key in SUBJECT_PREFIX:
            conj_class = conjugation_class.lower().strip() or "ø"
            class_prefixes = CONJ_PREFIX.get(conj_class, {})
            conj = class_prefixes.get(mode, "∅")

            parts = []
            if conj != "∅":
                parts.append(conj)

            subj = SUBJECT_PREFIX[subj_key]
            if subj != "∅-":
                parts.append(subj)

            cls = classifier if classifier and classifier != "ø" else "∅"
            if cls != "∅":
                parts.append(f"{cls}-")

            parts.append(f"√{root}[?]")
            mode_guesses[subj_key] = "".join(parts)

        result[mode] = mode_guesses
    return result


# ── Attested forms from paradigm data ─────────────────────────────────────────

import json
from pathlib import Path

_PARADIGM_FILE = Path(__file__).parent.parent / "data" / "paradigms_from_conjugator.jsonl"

_SUBJECT_FROM_NODE: dict[str, str] = {
    "x̱a-": "1sg",
    "i-":  "2sg",
    "∅-":  "3",
    "tu-": "1pl",
    "yi-": "2pl",
    "du-": "4h",
}

_MODE_MAP: dict[str, str] = {
    "progressive-imperfective+": "imperfective",
    "progressive-imperfective-": "imperfective",
    "imperfective+": "imperfective",
    "imperfective-": "imperfective",
    "perfective+":  "perfective",
    "perfective-":  "perfective",
    "habitual+":    "habitual",
    "habitual-":    "habitual",
    "future+":      "potential",
    "future-":      "potential",
    "imperative":   "imperative",
    "prohibitive":  "prohibitive",
}


def load_attested_forms() -> dict[str, dict[str, dict[str, dict]]]:
    """
    Load attested forms from paradigm data.

    Returns: {verb_root: {mode: {subject: {tlingit, english, source}}}}
    """
    if not _PARADIGM_FILE.exists():
        return {}

    result: dict = {}
    with open(_PARADIGM_FILE) as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue

            verb = r.get("verb", "")
            mode_raw = r.get("qualifiers", {}).get("mode", "")
            mode = _MODE_MAP.get(mode_raw, mode_raw)
            from_node = r.get("from_node", "")
            subject = _SUBJECT_FROM_NODE.get(from_node, from_node)

            tlingit = r.get("source_text", {}).get("text", "")
            english = next((
                t.get("text", "") for t in r.get("translations", [])
                if t.get("language") == "english"
            ), "")
            source = r.get("source_text", {}).get("source", "")

            if verb not in result:
                result[verb] = {}
            if mode not in result[verb]:
                result[verb][mode] = {}
            result[verb][mode][subject] = {
                "tlingit": tlingit,
                "english": english,
                "source": source,
            }

    return result
