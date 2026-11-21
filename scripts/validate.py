#!/usr/bin/env python3
"""Validate data/apis/*.yaml: JSON Schema + evidence rules. Exit 1 on any error."""
import json, sys, re
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator
sys.path.insert(0, str(Path(__file__).resolve().parent))
from verdict import compute

ROOT = Path(__file__).resolve().parent.parent
schema = json.loads((ROOT / "schema" / "api.schema.json").read_text())
V = Draft202012Validator(schema)
# a non-unknown value in these fields must be backed by evidence
EVIDENCE_FIELDS = ["commercial_use", "storage_caching", "redistribution_display", "attribution_required",
                   "data_license", "bulk_download", "self_host_option", "share_alike"]
errors, seen = [], set()
for f in sorted((ROOT / "data" / "apis").glob("*.yaml")):
    e = yaml.safe_load(f.read_text(encoding="utf-8"))
    err = lambda m: errors.append(f"{f.name}: {m}")
    if e.get("id") != f.stem: err("id must equal filename")
    if e.get("id") in seen: err("duplicate id")
    seen.add(e.get("id"))
    for x in V.iter_errors(e): err(x.message[:200])
    for k in ["commercial_use", "storage_caching", "redistribution_display", "attribution_required", "data_license"]:
        if k not in e: err(f"missing key {k} (use unknown)")
    ev = {i.get("field") for i in e.get("evidence", [])}
    for fld in EVIDENCE_FIELDS:
        if e.get(fld, "unknown") not in ("unknown", None) and fld not in ev:
            err(f"{fld}={e[fld]} has no evidence entry")
    for i in e.get("evidence", []):
        if len(i.get("quote", "").split()) > 25: err(f"quote for {i.get('field')} exceeds 25 words")
        if not str(i.get("url", "")).startswith("http"): err("evidence url must be http(s)")
    if e.get("verdict") != "unknown" and e.get("confidence") is None: err("verdict needs confidence")
    if e.get("verdict_override") and not e.get("override_reason"): err("verdict_override needs override_reason")
    if e.get("verdict") != compute(e): err(f"verdict {e.get('verdict')} != computed {compute(e)} (use verdict_override + override_reason)")
print(f"{len(seen)} entries, {len(errors)} errors")
for m in errors[:50]: print(" ", m)
sys.exit(1 if errors else 0)
