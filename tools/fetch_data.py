"""
Fetch language data from public sources.

Run this once to populate the data/ directory:
    python tools/fetch_data.py
"""

import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

SOURCES = {
    "tlingit_verbs_eggleston.xml": (
        "http://ankn.uaf.edu/~tlingitverbs/TlingitVerbsRoots.xml",
        "Eggleston verb database (575+ Tlingit verbs with paradigms)",
    ),
}

CORPUS_FILES = [
    ("001_Zuboff_R_-_Basket_Bay.txt",
     "https://raw.githubusercontent.com/jcrippen/tlingit-corpus/master/"
     "001%20Zuboff%20R%20-%20Basket%20Bay%20-%20Text.txt"),
    ("004_Naish_C_-_Tlingit_Verb_Dictionary.txt",
     "https://raw.githubusercontent.com/jcrippen/tlingit-corpus/master/"
     "004%20Naish%20C%20%26%20Story%20G%20-%20Tlingit%20Verb%20Dictionary%20-%20Text.txt"),
    ("010_Marks_W_-_Naatsilanei.txt",
     "https://raw.githubusercontent.com/jcrippen/tlingit-corpus/master/"
     "010%20Marks%20W%20-%20Naatsilanéi%20-%20Text.txt"),
    ("020_Katishan_-_Salmon_Boy.txt",
     "https://raw.githubusercontent.com/jcrippen/tlingit-corpus/master/"
     "020%20Katishan%20-%20Salmon%20Boy%20-%20Text.txt"),
]


def fetch(url: str, dest: Path, description: str) -> None:
    if dest.exists():
        print(f"  Already exists: {dest.name}")
        return
    print(f"  Fetching {description}...", end=" ", flush=True)
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"done ({dest.stat().st_size // 1024}KB)")
    except Exception as e:
        print(f"FAILED: {e}")


if __name__ == "__main__":
    print("Fetching Tlingit language data...")
    print()

    for filename, (url, desc) in SOURCES.items():
        fetch(url, DATA_DIR / filename, desc)

    print()
    print("Fetching corpus texts...")
    for filename, url in CORPUS_FILES:
        fetch(url, DATA_DIR / filename, filename)

    print()
    print("Done. Run: python -m tlingit.builder 'go'")
