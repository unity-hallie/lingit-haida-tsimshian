"""
Corpus search: find example sentences containing a Tlingit string.

Searches the Crippen corpus texts for lines containing the given
Tlingit word or root, and returns paired Tlingit/English lines
where available.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

DATA_DIR = Path(__file__).parent.parent / "data"


@dataclass
class ExampleSentence:
    source: str       # filename / speaker
    tlingit: str
    english: str = ""


def _load_pairs(text_path: Path) -> list[tuple[str, str]]:
    """
    Load paired (tlingit_line, english_line) from a corpus text file.
    Lines are numbered; we match by number.
    """
    lines: dict[int, str] = {}
    for raw in text_path.read_text(encoding="utf-8", errors="replace").splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("{"):
            continue
        m = re.match(r'^(\d+)\s+(.*)', raw)
        if m:
            lines[int(m.group(1))] = m.group(2)
    return list(lines.items())


def _load_translation(trans_path: Path) -> dict[int, str]:
    result: dict[int, str] = {}
    if not trans_path.exists():
        return result
    for raw in trans_path.read_text(encoding="utf-8", errors="replace").splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("{"):
            continue
        m = re.match(r'^(\d+)\s+(.*)', raw)
        if m:
            result[int(m.group(1))] = m.group(2)
    return result


def find_examples(
    search: str,
    limit: int = 5,
    data_dir: Path | None = None,
) -> list[ExampleSentence]:
    """
    Search corpus texts for lines containing `search`.
    Returns up to `limit` ExampleSentence objects with paired translations.
    """
    if data_dir is None:
        data_dir = DATA_DIR

    results: list[ExampleSentence] = []
    search_lower = search.lower()

    # Find text files and their translation partners
    for text_path in sorted(data_dir.glob("*.txt")):
        if "Translation" in text_path.name:
            continue  # skip translation files themselves
        if "Verb_Dictionary" in text_path.name:
            continue  # skip the verb dictionary text

        # Find matching translation file — same prefix, contains "Translation"
        prefix = text_path.stem.split("_-_")[0]
        possible_trans = list(data_dir.glob(f"{prefix}*Translation*.txt"))

        pairs = _load_pairs(text_path)
        translations: dict[int, str] = {}
        if possible_trans:
            translations = _load_translation(possible_trans[0])

        source = text_path.stem.replace("_", " ").split(" - ")[-1] if " - " in text_path.stem.replace("_", " ") else text_path.stem

        for num, tlingit_line in pairs:
            if search_lower in tlingit_line.lower():
                english = translations.get(num, "")
                results.append(ExampleSentence(
                    source=source,
                    tlingit=tlingit_line,
                    english=english,
                ))
                if len(results) >= limit:
                    return results

    return results
