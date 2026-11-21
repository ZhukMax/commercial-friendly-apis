#!/usr/bin/env python3
"""Apply data/second_pass/result-*.json to data/apis/*.yaml and write review-needed.md.
confirmed -> second_check: confirmed. disputed -> second_check: disputed, counter-evidence added to evidence,
suggested field values applied only when backed by a counter-evidence entry for that field,
verdict forced to yellow via verdict_override if the computed verdict is still green."""
import json, glob, datetime, sys
from pathlib import Path
import yaml
sys.path.insert(0, str(Path(__file__).resolve().parent))
from verdict import compute

ROOT = Path(__file__).resolve().parent.parent
TODAY = datetime.date.today().isoformat()
CORE = {"commercial_use", "storage_caching", "redistribution_display", "attribution_required", "share_alike"}
ENUMS = {"commercial_use": {"yes", "no", "paid-only", "ambiguous", "unknown"},
         "storage_caching": {"yes", "limited", "no", "ambiguous", "unknown"},
         "redistribution_display": {"yes", "no", "ambiguous", "unknown"},
         "attribution_required": {"yes", "no", "ambiguous", "unknown"},
         "share_alike": {"yes", "no", "unknown"}}
# my own rule: a confirmation that rests on an unread upstream/operator licence is not a confirmation
AUTH = {"none", "apiKey", "OAuth", "other", "unknown"}
# `commercial_use: no` is accepted only for explicit prohibitions; otherwise it is kept as ambiguous for human review
NO_OK = {"congressinvests", "bayan", "close-knit", "worldcoinindex"}
WEAK = {"bettip": "operator terms unreadable (empty to curl and browser)",
        "calendrier-tempo": "EDF and Open-Meteo upstream terms not verified",
        "searchpincode": "India Post/data.gov.in upstream licence could not be read"}

def load(i): return yaml.safe_load((ROOT / "data/apis" / f"{i}.yaml").read_text(encoding="utf-8"))
def save(e): (ROOT / "data/apis" / f"{e['id']}.yaml").write_text(
    yaml.safe_dump(e, sort_keys=False, allow_unicode=True, width=100), encoding="utf-8")

disputed, confirmed, changes = [], 0, []
for f in sorted(glob.glob(str(ROOT / "data/second_pass/result-*.json"))):
    for r in json.load(open(f)):
        e = load(r["id"])
        if e.get("second_check"): continue
        out = r["outcome"]
        if out == "confirmed" and r["id"] in WEAK:
            out = "disputed"; r.setdefault("reasons", []).append("could not re-verify: " + WEAK[r["id"]])
        reasons = "; ".join(r.get("reasons", []))[:600] or r.get("note", "")[:600]
        e["second_check_at"] = TODAY
        if out == "confirmed":
            e["second_check"] = "confirmed"; confirmed += 1
            if r.get("note"): e["second_check_note"] = r["note"][:400]
        else:
            e["second_check"] = "disputed"; e["second_check_note"] = reasons
            ev = e.setdefault("evidence", [])
            have = {(x["field"], x["quote"]) for x in ev}
            applied = []
            for ce in r.get("counter_evidence", []):
                fld = ce.get("field") or "second_check"
                q = ce["quote"]
                if len(q.split()) > 25 or (fld, q) in have or not str(ce.get("url", "")).startswith("http"): continue
                ev.append({"field": fld, "url": ce["url"], "quote": q, "checked_at": TODAY}); have.add((fld, q))
            fields_with_ev = {x["field"] for x in ev}
            for k, v in (r.get("suggested") or {}).items():
                if k == "auth" and v in AUTH:
                    e["auth"] = v; applied.append(f"auth={v}"); continue
                if k not in ENUMS or v not in ENUMS[k]: continue
                if k == "commercial_use" and v == "no" and e["id"] not in NO_OK:
                    v = "ambiguous"
                    applied.append("commercial_use=ambiguous (suggested no, needs human review)")
                    e[k] = v; continue
                if v == "unknown" or k in fields_with_ev:
                    e[k] = v; applied.append(f"{k}={v}")
            if applied: e["second_check_note"] += " | applied: " + ", ".join(applied)
            before = e["verdict"]
            e["verdict"] = compute(e)
            if e["verdict"] == "green":
                e["verdict_override"] = "yellow"; e["override_reason"] = ("Second check: " + reasons)[:500]
            e["verdict"] = compute(e)
            if before == "yellow" and e["verdict"] == "unknown" and e.get("commercial_use") not in (None, "unknown"):
                # more resolved fields must not make an entry look worse: remaining silence keeps it yellow
                e["verdict_override"] = "yellow"
                e["override_reason"] = "Second check resolved some fields; unconfirmed storage/display keeps it at yellow."
                e["verdict"] = compute(e)
            if before != e["verdict"]: changes.append((e["id"], before, e["verdict"]))
            disputed.append((e["id"], e["name"], e["verdict"], reasons, r.get("counter_evidence", [])))
        save(e)
print("confirmed", confirmed, "disputed", len(disputed))
print("verdict changes:", [f"{i}:{a}->{b}" for i, a, b in changes])
json.dump([d[0] for d in disputed], open(ROOT / "data/second_pass/disputed_ids.json", "w"))
