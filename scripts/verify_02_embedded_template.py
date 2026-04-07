#!/usr/bin/env python3
"""Verify notebook 02 embedded Genie template matches templates/manufacturing_genie_configured.json."""
import base64
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "manufacturing_genie_configured.json"
NB = ROOT / "notebooks" / "02_create_genie_spaces.ipynb"


def main() -> int:
    if not TEMPLATE.is_file():
        print("ERROR: missing", TEMPLATE, file=sys.stderr)
        return 1
    if not NB.is_file():
        print("ERROR: missing", NB, file=sys.stderr)
        return 1

    expected = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    expected_b64 = base64.b64encode(
        TEMPLATE.read_bytes()
    ).decode("ascii")

    nb = json.loads(NB.read_text(encoding="utf-8"))
    src = ""
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        block = "".join(cell.get("source", []))
        if "_EMBEDDED_B64" in block:
            src = block
            break
    if not src:
        print("ERROR: no code cell with _EMBEDDED_B64 in", NB, file=sys.stderr)
        return 1

    m = re.search(r'_EMBEDDED_B64 = "([A-Za-z0-9+/=]+)"', src)
    if not m:
        print("ERROR: could not parse _EMBEDDED_B64 string from notebook", file=sys.stderr)
        return 1

    embedded_b64 = m.group(1)
    if embedded_b64 != expected_b64:
        print(
            "ERROR: embedded base64 in notebook does not match templates file.",
            "Run: python3 scripts/build_02_notebook.py",
            file=sys.stderr,
        )
        return 1

    decoded = json.loads(base64.b64decode(embedded_b64).decode("utf-8"))
    for key in ("sql_instructions", "sample_questions", "curated_questions"):
        if key not in decoded:
            print(f"ERROR: decoded template missing key {key!r}", file=sys.stderr)
            return 1

    if decoded != expected:
        print(
            "ERROR: decoded JSON differs from templates file (normalize issue?).",
            file=sys.stderr,
        )
        return 1

    print("OK: embedded template in 02 matches templates/manufacturing_genie_configured.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
