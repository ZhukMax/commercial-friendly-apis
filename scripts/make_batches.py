#!/usr/bin/env python3
"""Split unchecked, live, priority-category entries into batches (data/batches/batch-NNN.txt)."""
import yaml, glob, collections
from pathlib import Path
from urllib.parse import urlsplit
ROOT = Path(__file__).resolve().parent.parent
PRIORITY = ["Government", "Open Data", "Geocoding", "Weather", "Environment", "Transportation", "Health",
            "Science & Math", "Finance", "Food & Drink", "Books", "Business"]
SIZE = 25
E = [yaml.safe_load(open(f)) for f in glob.glob(str(ROOT / "data/apis/*.yaml"))]
elig = [e for e in E if e["category"] in PRIORITY and e.get("link_status") != "dead" and not e.get("checked_at")]
host = lambda e: (urlsplit(e["url"]).hostname or "").replace("www.", "")
elig.sort(key=lambda e: (PRIORITY.index(e["category"]), host(e), e["name"].lower()))
out = ROOT / "data" / "batches"; out.mkdir(exist_ok=True)
for f in out.glob("*.txt"): f.unlink()
for n, i in enumerate(range(0, len(elig), SIZE), 1):
    chunk = elig[i:i + SIZE]
    (out / f"batch-{n:03d}.txt").write_text("\n".join(e["id"] for e in chunk) + "\n")
print(len(elig), "entries,", (len(elig) + SIZE - 1) // SIZE, "batches")
print(collections.Counter(e["category"] for e in elig))
