"""
Local web server for the Lingít verb builder.

Runs on your Mac Mini; accessible from any device on the same WiFi.
Speaker corrections are saved to data/speaker_corrections.json.

Usage:
    python app.py
    python app.py --host 0.0.0.0 --port 5000   # LAN access
    python app.py --debug
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

# ── Paths ─────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
CORRECTIONS_FILE = DATA_DIR / "speaker_corrections.json"

# Lazy-loaded globals
_db = None
_attested = None

app = Flask(__name__, static_folder=str(ROOT / "docs"), static_url_path="")


# ── Data loading ──────────────────────────────────────────────────────────────

def get_db():
    global _db
    if _db is None:
        from tlingit.verbs import VerbDatabase
        path = DATA_DIR / "tlingit_verbs_eggleston.xml"
        _db = VerbDatabase.load(path)
    return _db


def get_attested():
    global _attested
    if _attested is None:
        from tlingit.guesses import load_attested_forms
        _attested = load_attested_forms()
    return _attested


def load_corrections() -> dict:
    if CORRECTIONS_FILE.exists():
        try:
            return json.loads(CORRECTIONS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_corrections(data: dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    CORRECTIONS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ── API routes ────────────────────────────────────────────────────────────────

@app.get("/api/search")
def api_search():
    """Search verb themes by English keyword or Tlingit root."""
    q = request.args.get("q", "").strip()
    root = request.args.get("root", "").strip()
    limit = min(int(request.args.get("limit", 10)), 50)

    db = get_db()
    attested = get_attested()
    corrections = load_corrections()

    if root:
        entry = db.root(root)
        themes = entry.themes if entry else []
    elif q:
        themes = db.find(q, limit=limit)
    else:
        return jsonify({"error": "provide q or root parameter"}), 400

    from tlingit.guesses import make_all_guesses
    from tlingit.corpus import find_examples

    results = []
    for theme in themes:
        examples = find_examples(theme.root, limit=3)
        guesses = make_all_guesses(theme.root, theme.conjugation_class, theme.classifier)
        att = attested.get(theme.root, {})
        corr = corrections.get(theme.root, {})

        results.append({
            "root": theme.root,
            "theme": theme.theme_str,
            "gloss": theme.gloss,
            "conjugation_class": theme.conjugation_class,
            "verb_type": theme.verb_type,
            "classifier": theme.classifier,
            "prefixes": theme.prefixes,
            "has_stem_variation": theme.has_stem_variation,
            "examples": [
                {"source": e.source, "tlingit": e.tlingit, "english": e.english}
                for e in examples
            ],
            "guesses": guesses,
            "attested": att,
            "corrections": corr,
        })

    return jsonify({"results": results, "count": len(results)})


@app.get("/api/correction/<root>")
def api_get_correction(root: str):
    """Get all speaker corrections for a root."""
    corrections = load_corrections()
    return jsonify(corrections.get(root, {}))


@app.post("/api/correction/<root>")
def api_save_correction(root: str):
    """
    Save a speaker correction.

    Body: {"mode": "perfective", "subject": "1sg", "form": "wusgút", "note": "..."}
    """
    body = request.get_json(silent=True) or {}
    mode = body.get("mode", "").strip()
    subject = body.get("subject", "").strip()
    form = body.get("form", "").strip()
    note = body.get("note", "").strip()

    if not (mode and subject and form):
        return jsonify({"error": "mode, subject, and form are required"}), 400

    corrections = load_corrections()
    if root not in corrections:
        corrections[root] = {}
    if mode not in corrections[root]:
        corrections[root][mode] = {}

    corrections[root][mode][subject] = {"form": form, "note": note}
    save_corrections(corrections)

    return jsonify({"ok": True, "saved": corrections[root][mode][subject]})


@app.delete("/api/correction/<root>/<mode>/<subject>")
def api_delete_correction(root: str, mode: str, subject: str):
    """Delete a single speaker correction."""
    corrections = load_corrections()
    try:
        del corrections[root][mode][subject]
        save_corrections(corrections)
        return jsonify({"ok": True})
    except KeyError:
        return jsonify({"ok": True, "note": "not found"})


@app.get("/api/corrections/export")
def api_export_corrections():
    """Export all corrections as a JSON download."""
    corrections = load_corrections()
    response = app.response_class(
        response=json.dumps(corrections, ensure_ascii=False, indent=2),
        status=200,
        mimetype="application/json",
    )
    response.headers["Content-Disposition"] = "attachment; filename=speaker_corrections.json"
    return response


@app.post("/api/corrections/import")
def api_import_corrections():
    """
    Import corrections (e.g. exported from the static demo).

    Body: the JSON object exported from localStorage.
    Merges with existing corrections; speaker corrections win over guesses.
    """
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": "expected JSON object"}), 400

    corrections = load_corrections()

    # Merge: incoming data may use key format "root__mode__subject" (localStorage)
    # or nested {root: {mode: {subject: {form, note}}}} (server format)
    added = 0
    for key, value in body.items():
        if "__" in key:
            # localStorage flat key: "gut__perfective__1sg"
            parts = key.split("__")
            if len(parts) == 3:
                root, mode, subject = parts
                if root not in corrections:
                    corrections[root] = {}
                if mode not in corrections[root]:
                    corrections[root][mode] = {}
                corrections[root][mode][subject] = {
                    "form": value if isinstance(value, str) else value.get("form", ""),
                    "note": value.get("note", "") if isinstance(value, dict) else "",
                }
                added += 1
        elif isinstance(value, dict):
            # Nested format
            root = key
            if root not in corrections:
                corrections[root] = {}
            for mode, subjects in value.items():
                if isinstance(subjects, dict):
                    if mode not in corrections[root]:
                        corrections[root][mode] = {}
                    for subject, entry in subjects.items():
                        corrections[root][mode][subject] = entry
                        added += 1

    save_corrections(corrections)
    return jsonify({"ok": True, "added": added})


@app.get("/api/status")
def api_status():
    db = get_db()
    corrections = load_corrections()
    total_corrections = sum(
        len(subjects)
        for modes in corrections.values()
        for subjects in modes.values()
    )
    return jsonify({
        "themes": db.total_themes,
        "roots": len(db.entries),
        "corrections": total_corrections,
        "corrections_file": str(CORRECTIONS_FILE),
    })


# ── Static files ──────────────────────────────────────────────────────────────

@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Lingít verb builder — local server")
    parser.add_argument("--host", default="0.0.0.0",
                        help="Host to bind (default 0.0.0.0 = all interfaces)")
    parser.add_argument("--port", type=int, default=5000, help="Port (default 5000)")
    parser.add_argument("--debug", action="store_true", help="Flask debug mode")
    args = parser.parse_args()

    # Warm up the database
    print("Loading verb database...", end=" ", flush=True)
    db = get_db()
    print(f"{db.total_themes} themes loaded.")

    if args.host == "0.0.0.0":
        import socket
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except Exception:
            local_ip = "your-mac-mini-ip"
        print(f"\nOpen on this machine: http://localhost:{args.port}")
        print(f"Open on your phone:   http://{local_ip}:{args.port}")
    else:
        print(f"\nOpen: http://{args.host}:{args.port}")

    print(f"Speaker corrections: {CORRECTIONS_FILE}\n")

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
