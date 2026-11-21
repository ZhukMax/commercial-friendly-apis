#!/usr/bin/env python3
"""Second-pass queue: green entries first, then entries with an ambiguous core field."""
import yaml, glob
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
core = ["commercial_use", "storage_caching", "redistribution_display", "attribution_required"]
E = [yaml.safe_load(open(f)) for f in glob.glob(str(ROOT / "data/apis/*.yaml"))]
E = [e for e in E if e.get("checked_at") and not e.get("second_check")]
green = sorted(e["id"] for e in E if e["verdict"] == "green")
amb = sorted(e["id"] for e in E if e["verdict"] != "green" and any(e.get(k) == "ambiguous" for k in core))
out = ROOT / "data" / "second_pass"; out.mkdir(exist_ok=True)
import sys
start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
n = start - 1
for grp in (green, amb):
    for i in range(0, len(grp), 25):
        n += 1; (out / f"queue-{n:03d}.txt").write_text("\n".join(grp[i:i + 25]) + "\n")
print(len(green), "green,", len(amb), "ambiguous ->", n - start + 1, "queues from", start)
