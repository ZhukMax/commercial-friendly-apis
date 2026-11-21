#!/usr/bin/env python3
"""HTTP-check every entry's url; write status into data/apis/*.yaml and data/link_report.json."""
import asyncio, json, datetime, collections
from pathlib import Path
import httpx, yaml

ROOT = Path(__file__).resolve().parent.parent
FILES = sorted((ROOT / "data" / "apis").glob("*.yaml"))
TODAY = datetime.date.today().isoformat()
UA = {"User-Agent": "Mozilla/5.0 (compatible; commercial-friendly-apis link checker; +https://github.com/)"}

async def probe(client, url):
    last = None
    for method in ("HEAD", "GET"):
        try:
            r = await client.request(method, url, follow_redirects=True, headers=UA)
            code = r.status_code
            if method == "HEAD" and code in (403, 404, 405, 406, 429, 500, 501, 503):
                last = code; continue
            return code, str(r.url), None
        except httpx.HTTPError as e:
            last = type(e).__name__
            if method == "GET":
                return None, None, last
    return (last if isinstance(last, int) else None), None, (None if isinstance(last, int) else last)

def classify(url, code, final, err):
    if err: return "dead", err
    if code is None: return "dead", "no response"
    if code in (404, 410) or code >= 500: return "dead", f"HTTP {code}"
    if code in (401, 403, 429, 451, 999): return "alive", f"HTTP {code} (blocked for bots, assumed alive)"
    if code >= 400: return "dead", f"HTTP {code}"
    norm = lambda u: u.split("://", 1)[-1].split("#")[0].rstrip("/").lower().replace("www.", "", 1)
    if final and norm(final) != norm(url): return "redirect", f"-> {final}"
    return "alive", ""

async def main():
    entries = [(f, yaml.safe_load(f.read_text(encoding="utf-8"))) for f in FILES]
    sem = asyncio.Semaphore(40)
    limits = httpx.Limits(max_connections=60)
    async with httpx.AsyncClient(timeout=httpx.Timeout(12.0), limits=limits, verify=True) as client:
        async def one(f, e):
            async with sem:
                code, final, err = await probe(client, e["url"])
            st, note = classify(e["url"], code, final, err)
            e["link_status"], e["link_checked_at"] = st, TODAY
            if note: e["link_note"] = note
            else: e.pop("link_note", None)
            f.write_text(yaml.safe_dump(e, sort_keys=False, allow_unicode=True, width=100), encoding="utf-8")
            return e["id"], st, note
        res = await asyncio.gather(*(one(f, e) for f, e in entries))
    cnt = collections.Counter(s for _, s, _ in res)
    rep = {"checked_at": TODAY, "counts": cnt, "dead": [(i, n) for i, s, n in res if s == "dead"]}
    (ROOT / "data" / "link_report.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    print(dict(cnt))

asyncio.run(main())
