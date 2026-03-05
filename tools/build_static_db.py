"""
Build docs/tlingit_db.json — the full verb database for the static page.

Reads:
  data/tlingit_verbs_eggleston.xml   → 978 verb themes
  data/all_verbs.jsonl               → attested forms from Haa Wsineix̲

Writes:
  docs/tlingit_db.json               → compact JSON for the browser

Usage:
    python tools/build_static_db.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"

sys.path.insert(0, str(ROOT))


def build():
    # ── Load verb themes ──────────────────────────────────────────────────────
    print("Loading verb database...", end=" ", flush=True)
    from tlingit.verbs import VerbDatabase
    db = VerbDatabase.load(DATA / "tlingit_verbs_eggleston.xml")
    print(f"{db.total_themes} themes, {len(db.entries)} roots")

    themes = []
    for entry in db.entries:
        for theme in entry.themes:
            themes.append({
                "root":              theme.root,
                "theme":             theme.theme_str,
                "gloss":             theme.gloss,
                "conjugation_class": theme.conjugation_class,
                "verb_type":         theme.verb_type,
                "classifier":        theme.classifier,
                "prefixes":          theme.prefixes,
                "stem_varies":       theme.has_stem_variation,
            })

    # ── Load attested forms ───────────────────────────────────────────────────
    print("Loading attested forms...", end=" ", flush=True)
    from tlingit.guesses import load_attested_forms
    attested = load_attested_forms()
    print(f"{sum(len(m) for v in attested.values() for m in v.values())} forms across {len(attested)} roots")

    # Also load all_verbs.jsonl if present (wider than paradigms_from_conjugator.jsonl)
    all_verbs_path = DATA / "all_verbs.jsonl"
    if all_verbs_path.exists():
        _MODE_MAP = {
            "progressive-imperfective+": "imperfective",
            "progressive-imperfective-": "imperfective",
            "imperfective+": "imperfective",
            "imperfective-": "imperfective",
            "perfective+":   "perfective",
            "perfective-":   "perfective",
            "habitual+":     "habitual",
            "habitual-":     "habitual",
            "future+":       "potential",
            "future-":       "potential",
            "imperative":    "imperative",
            "prohibitive":   "prohibitive",
        }
        _SUBJ_MAP = {
            "x̱a-": "1sg",
            "i-":  "2sg",
            "∅-":  "3",
            "tu-": "1pl",
            "yi-": "2pl",
            "du-": "4h",
        }
        extra = 0
        with open(all_verbs_path) as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                verb = r.get("verb", "")
                q = r.get("qualifiers", {})
                mode_raw = q.get("mode", "")
                mode = _MODE_MAP.get(mode_raw, mode_raw)
                from_node = r.get("from_node", "")
                subject = _SUBJ_MAP.get(from_node, from_node)
                tlingit = r.get("source_text", {}).get("text", "")
                english = next((
                    t.get("text", "") for t in r.get("translations", [])
                    if t.get("language") == "english"
                ), "")
                source = r.get("source_text", {}).get("source", "")

                if verb and mode and subject and tlingit:
                    if verb not in attested:
                        attested[verb] = {}
                    if mode not in attested[verb]:
                        attested[verb][mode] = {}
                    if subject not in attested[verb][mode]:
                        attested[verb][mode][subject] = {
                            "tlingit": tlingit,
                            "english": english,
                            "source": source,
                        }
                        extra += 1
        print(f"  + {extra} forms from all_verbs.jsonl")

    # ── Build corpus index (root → [tlingit, english, source]) ───────────────
    print("Building corpus index...", end=" ", flush=True)
    from tlingit.corpus import find_examples
    corpus_index: dict[str, list] = {}
    roots_with_examples = 0
    for entry in db.entries:
        examples = find_examples(entry.root, limit=3)
        if examples:
            corpus_index[entry.root] = [
                {"tlingit": e.tlingit, "english": e.english, "source": e.source}
                for e in examples
            ]
            roots_with_examples += 1
    print(f"{roots_with_examples} roots have corpus examples")

    # ── Write output ──────────────────────────────────────────────────────────
    out = {
        "meta": {
            "themes":   len(themes),
            "roots":    len(db.entries),
            "attested": sum(
                len(subjects)
                for modes in attested.values()
                for subjects in modes.values()
            ),
            "sources": [
                "Eggleston (2013) via UAF/ANLC",
                "Haa Wsineix̲ (Dauenhauer & Dauenhauer) via Twitchell Conjugator",
                "Crippen corpus (jcrippen/tlingit-corpus)",
            ],
        },
        "themes":   themes,
        "attested": attested,
        "corpus":   corpus_index,
    }

    out_path = DOCS / "tlingit_db.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    size_kb = out_path.stat().st_size / 1024
    print(f"\nWrote {out_path} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    build()
