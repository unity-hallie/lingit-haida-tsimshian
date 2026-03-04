"""
Tlingit verb builder — interactive structural exploration.

Given an English concept, finds the relevant verb themes,
explains their structure, and shows corpus examples.

This is phase 1: structure + examples.
Phase 2 will add full paradigm conjugation (requires stem alternation data
from Xunei or native speaker paradigms — these cannot be computed).

Usage:
    python -m tlingit.builder "go"
    python -m tlingit.builder "eat"
    python -m tlingit.builder --root aat
"""

from __future__ import annotations

import sys
from pathlib import Path

from .verbs import VerbDatabase
from .corpus import find_examples


def run_builder(
    query: str | None = None,
    root: str | None = None,
    show_examples: bool = True,
    limit: int = 5,
) -> None:
    """Run the interactive verb builder."""

    print("═" * 62)
    print("  LINGÍT VERB BUILDER")
    print("  Structural analysis + corpus examples")
    print("  Data: Eggleston (575+ verbs) · Crippen corpus")
    print("═" * 62)

    # Load database
    db_path = Path(__file__).parent.parent / "data" / "tlingit_verbs_eggleston.xml"
    if not db_path.exists():
        print(f"\n  Data file not found: {db_path}")
        print("  Run: python tools/fetch_data.py")
        return

    print(f"\n  Loading verb database...", end=" ", flush=True)
    db = VerbDatabase.load(db_path)
    print(f"{db.total_themes} verb themes loaded.")

    # Find themes
    if root:
        entry = db.root(root)
        if not entry:
            print(f"\n  Root '{root}' not found.")
            return
        themes = entry.themes
        print(f"\n  Root: .{root}  ({len(themes)} theme(s))")
    elif query:
        themes = db.find(query, limit=limit)
        if not themes:
            print(f"\n  No verbs found for '{query}'.")
            return
        print(f"\n  Search: '{query}'  →  {len(themes)} result(s)")
    else:
        print("\n  Provide a query (English) or --root (Tlingit root).")
        return

    # Display themes
    print()
    for i, theme in enumerate(themes, 1):
        print(f"  {'─' * 58}")
        print(f"  [{i}] Root: .{theme.root}")
        for line in theme.explain().splitlines():
            print(f"      {line}")

        # Corpus examples
        if show_examples:
            examples = find_examples(theme.root, limit=2)
            if examples:
                print(f"\n      Examples from corpus:")
                for ex in examples:
                    print(f"        Lingít:  {ex.tlingit}")
                    if ex.english:
                        print(f"        English: {ex.english}")
                    print(f"        Source:  {ex.source}")
                    print()
        print()

    print("  " + "─" * 58)
    print("  NOTE: Conjugated surface forms (perfective, imperfective,")
    print("  potential, etc.) require stem alternation data that must")
    print("  come from native speakers. This tool shows the structure;")
    print("  the community fills in the forms.")
    print("═" * 62)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Lingít verb builder — structural analysis and corpus examples"
    )
    parser.add_argument("query", nargs="?", help="English word to search for")
    parser.add_argument("--root", "-r", help="Tlingit verb root (e.g. aat, gut)")
    parser.add_argument("--no-examples", action="store_true", help="Skip corpus examples")
    parser.add_argument("--limit", "-n", type=int, default=5, help="Max results")
    args = parser.parse_args()

    if not args.query and not args.root:
        parser.print_help()
        sys.exit(1)

    run_builder(
        query=args.query,
        root=args.root,
        show_examples=not args.no_examples,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
