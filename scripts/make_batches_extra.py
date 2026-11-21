#!/usr/bin/env python3
"""Queue for the 'useful' non-priority categories (agreed with the maintainer): batch-037+ (existing batches untouched)."""
import yaml, glob, collections, sys
from pathlib import Path
from urllib.parse import urlsplit
ROOT = Path(__file__).resolve().parent.parent
USEFUL = sys.argv[1].split("|") if len(sys.argv) > 1 else ["Cryptocurrency", "Currency Exchange", "Blockchain", "News", "Jobs", "Education", "Events", "Sports & Fitness",
          "Patent", "Disasters", "Vehicle", "Dictionaries", "Shopping", "Open Source Projects", "Data Validation",
          "Calendar", "Art & Design"]
SIZE = 25
E = [yaml.safe_load(open(f)) for f in glob.glob(str(ROOT / "data/apis/*.yaml"))]
queued = {l.strip() for f in glob.glob(str(ROOT / "data/batches/batch-*.txt")) for l in open(f)}
elig = [e for e in E if e["category"] in USEFUL and e.get("link_status") != "dead" and not e.get("checked_at") and e.get("applicable") is not False and e["id"] not in queued]
host = lambda e: (urlsplit(e["url"]).hostname or "").replace("www.", "")
elig.sort(key=lambda e: (USEFUL.index(e["category"]), host(e), e["name"].lower()))
start = 1 + max(int(Path(f).stem.split("-")[1]) for f in glob.glob(str(ROOT / "data/batches/batch-*.txt")))
for k, i in enumerate(range(0, len(elig), SIZE)):
    (ROOT / "data/batches" / f"batch-{start + k:03d}.txt").write_text("\n".join(e["id"] for e in elig[i:i + SIZE]) + "\n")
print(len(elig), "entries ->", (len(elig) + SIZE - 1) // SIZE, "batches from", start)
print(collections.Counter(e["category"] for e in elig))
