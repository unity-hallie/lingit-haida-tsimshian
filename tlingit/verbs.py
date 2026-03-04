"""
Tlingit verb data loader and structural decomposition.

Parses the Eggleston/Leer verb database (XML) and provides
lookup by English gloss and structural decomposition of verb themes.

Verb themes follow the notation:
  PREFIX_CHAIN-CLASSIFIER-.ROOT~ (conjugation_class type)

Where:
  ~ = stem variation marker (stem changes by mode)
  conjugation_class = ø, na, ga, or ga (four unpredictable classes)
  type = act, event, state, motion, position

This module does NOT generate conjugated surface forms — stem alternation
and prefix contraction are unpredictable and require native speaker data.
What it does: structural analysis, English lookup, example sentences.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET


DATA_DIR = Path(__file__).parent.parent / "data"


# ── Verb theme decomposition ──────────────────────────────────────────────────

# The four conjugation classes (unpredictable per verb)
CONJUGATION_CLASSES = {
    "ø":  "zero conjugation (Ø-class)",
    "na": "na-conjugation",
    "ga": "ga-conjugation",
    "yi": "yi-conjugation",
}

# Thematic prefixes and what they encode
THEMATIC_PREFIXES = {
    "ka":  "surface / horizontal extent",
    "ya":  "face / front",
    "ji":  "hand / manual action",
    "tu":  "inside / mind / emotions",
    "x'a": "mouth / speech / eating",
    "ku":  "weather / environment",
    "sha": "head / top",
    "kei": "upward / becoming",
    "yei": "downward",
    "daak": "out to sea / away from shore",
    "yan":  "to rest / completion",
    "át":   "around / about",
    "neil": "inside / home",
    "yán":  "ashore / to land",
}

# Classifiers (directly before stem): voice and valency
CLASSIFIERS = {
    "ø":  "active, intransitive or transitive",
    "l":  "active voice, valency-increasing",
    "s":  "active voice, causative",
    "d":  "middle voice (reflexive/reciprocal/passive)",
    "sh": "reflexive",
    "l-s": "causative + active",
    "d-s": "middle + causative",
}

# Verb types
VERB_TYPES = {
    "act":      "activity (ongoing, unbounded)",
    "event":    "event (punctual, bounded)",
    "state":    "state (static, stative)",
    "motion":   "motion (directed movement)",
    "position": "position (spatial configuration)",
}


@dataclass
class VerbTheme:
    """
    A single Tlingit verb theme with structural analysis.

    theme_str: raw theme notation, e.g. "O-S-s-.aa~ (na act)"
    gloss: English meaning
    root: the verb root (e.g. "aa")
    conjugation_class: ø, na, ga, or yi
    verb_type: act, event, state, motion, position
    classifier: the classifier morpheme
    prefixes: list of prefix elements in order
    has_stem_variation: whether ~ appears (stem changes by mode)
    """
    theme_str: str
    gloss: str
    root: str
    conjugation_class: str = "ø"
    verb_type: str = ""
    classifier: str = "ø"
    prefixes: list[str] = field(default_factory=list)
    has_stem_variation: bool = False

    def explain(self) -> str:
        """Human-readable structural explanation."""
        lines = []
        lines.append(f"Theme:    {self.theme_str}")
        lines.append(f"Meaning:  {self.gloss}")
        lines.append(f"Root:     .{self.root}")

        if self.conjugation_class in CONJUGATION_CLASSES:
            lines.append(f"Class:    {CONJUGATION_CLASSES[self.conjugation_class]}")

        if self.verb_type in VERB_TYPES:
            lines.append(f"Type:     {VERB_TYPES[self.verb_type]}")

        if self.classifier in CLASSIFIERS:
            lines.append(f"Classifier: {self.classifier}– ({CLASSIFIERS[self.classifier]})")

        if self.prefixes:
            prefix_notes = []
            for p in self.prefixes:
                clean = p.rstrip("~").lstrip("-")
                if clean in THEMATIC_PREFIXES:
                    prefix_notes.append(f"{p} [{THEMATIC_PREFIXES[clean]}]")
                elif clean in ("O", "S", "P", "N"):
                    labels = {"O": "object", "S": "subject", "P": "place", "N": "noun"}
                    prefix_notes.append(f"{p} [{labels[clean]} slot]")
                else:
                    prefix_notes.append(p)
            lines.append(f"Prefixes: {' – '.join(prefix_notes)}")

        if self.has_stem_variation:
            lines.append("Note:     stem changes form by mode (unpredictable — must be learned)")

        return "\n".join(lines)


def _parse_theme(theme_str: str, root: str) -> VerbTheme:
    """Parse a raw theme string into a VerbTheme."""
    # Extract conjugation class and type from parenthetical
    # e.g. "(na act)" or "(ø motion)"
    conj_class = "ø"
    verb_type = ""
    paren_match = re.search(r'\(([^)]+)\)', theme_str)
    if paren_match:
        parts = paren_match.group(1).split()
        if parts:
            conj_class = parts[0]
        if len(parts) > 1:
            verb_type = parts[1]

    # Remove parenthetical for prefix analysis
    core = re.sub(r'\s*\([^)]*\)', '', theme_str).strip()

    # Has stem variation?
    has_variation = '~' in core

    # Find classifier: look for pattern -X-.root where X is classifier
    classifier = "ø"
    classifier_match = re.search(r'-([dlsø]+)-\.' + re.escape(root), core)
    if classifier_match:
        classifier = classifier_match.group(1)

    # Extract prefix chain (everything before the classifier+root)
    prefix_part = re.sub(r'-?[dlsø]*-?\.' + re.escape(root) + r'~?', '', core)
    prefixes = [p for p in re.split(r'[\s-]+', prefix_part) if p and p not in ('', '~')]

    return VerbTheme(
        theme_str=theme_str,
        gloss="",  # filled in by caller
        root=root,
        conjugation_class=conj_class,
        verb_type=verb_type,
        classifier=classifier,
        prefixes=prefixes,
        has_stem_variation=has_variation,
    )


# ── Verb entry ────────────────────────────────────────────────────────────────

@dataclass
class VerbEntry:
    """A verb root with all its themes."""
    root: str
    themes: list[VerbTheme] = field(default_factory=list)

    def search(self, english: str) -> list[VerbTheme]:
        """Find themes whose gloss contains the English word."""
        english = english.lower()
        return [t for t in self.themes if english in t.gloss.lower()]


# ── Database ──────────────────────────────────────────────────────────────────

class VerbDatabase:
    """
    Loaded verb database from the Eggleston XML.

    Usage:
        db = VerbDatabase.load()
        results = db.find("go")
        for theme in results:
            print(theme.explain())
    """

    def __init__(self, entries: list[VerbEntry]):
        self.entries = entries
        self._by_root: dict[str, VerbEntry] = {e.root: e for e in entries}
        # Build English index
        self._english_index: dict[str, list[VerbTheme]] = {}
        for entry in entries:
            for theme in entry.themes:
                for word in re.findall(r'\b\w+\b', theme.gloss.lower()):
                    self._english_index.setdefault(word, []).append(theme)

    @classmethod
    def load(cls, path: Path | None = None) -> VerbDatabase:
        """Load from the Eggleston XML file (parsed as text — it's XHTML with custom tags)."""
        if path is None:
            path = DATA_DIR / "tlingit_verbs_eggleston.xml"

        text = path.read_text(encoding="utf-8", errors="replace")

        entries: list[VerbEntry] = []
        current_root: str | None = None
        current_themes: list[VerbTheme] = []
        current_theme_str: str | None = None

        # Parse line by line — extract tag content with regex
        root_re    = re.compile(r'<Root>(.+?)</Root>')
        theme_re   = re.compile(r'<theme>(.+?)</theme>')
        gloss_re   = re.compile(r'<gloss_theme>(.+?)(?:</gloss_theme>|$)', re.DOTALL)

        i = 0
        lines = text.splitlines()
        while i < len(lines):
            line = lines[i]

            m = root_re.search(line)
            if m:
                if current_root and current_themes:
                    entries.append(VerbEntry(root=current_root, themes=current_themes))
                raw = m.group(1).strip()
                # "aa1 (3)" → "aa", "aak̲w (7)" → "aak̲w"
                current_root = re.sub(r'\s*\(.*\)', '', raw).strip().rstrip('0123456789 ').strip()
                current_themes = []
                current_theme_str = None
                i += 1
                continue

            m = theme_re.search(line)
            if m:
                current_theme_str = m.group(1).strip()
                i += 1
                continue

            m = gloss_re.search(line)
            if m and current_theme_str and current_root:
                gloss = m.group(1).strip()
                # Collect continuation lines until closing tag or next tag
                while '</gloss_theme>' not in lines[i] and i + 1 < len(lines):
                    i += 1
                    next_line = lines[i].strip()
                    if re.search(r'<[A-Za-z]', next_line):
                        break
                    gloss = gloss + " " + next_line
                gloss = re.sub(r'</gloss_theme>.*', '', gloss).strip()
                gloss = gloss.replace("&apos;", "'").replace("&amp;", "&").replace("&lt;", "<")
                if gloss:
                    theme = _parse_theme(current_theme_str, current_root)
                    theme.gloss = gloss
                    current_themes.append(theme)
                current_theme_str = None

            i += 1

        if current_root and current_themes:
            entries.append(VerbEntry(root=current_root, themes=current_themes))

        return cls(entries)

    def find(self, english: str, limit: int = 10) -> list[VerbTheme]:
        """Find verb themes by English keyword."""
        english = english.lower().strip()
        results = self._english_index.get(english, [])
        # Also try partial match
        if not results:
            results = [
                t for themes in self._english_index.values()
                for t in themes
                if english in t.gloss.lower()
            ]
        seen = set()
        unique = []
        for t in results:
            key = (t.root, t.theme_str)
            if key not in seen:
                seen.add(key)
                unique.append(t)
        return unique[:limit]

    def root(self, root_str: str) -> VerbEntry | None:
        """Look up a verb entry by root."""
        return self._by_root.get(root_str)

    @property
    def total_themes(self) -> int:
        return sum(len(e.themes) for e in self.entries)
