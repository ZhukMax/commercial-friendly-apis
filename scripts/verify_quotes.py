#!/usr/bin/env python3
"""Check that each evidence.quote literally appears on its evidence.url.
Usage: verify_quotes.py [id ...]   (default: all entries that have evidence)
Statuses: ok | missing (page fetched, quote not found) | unfetchable (error / empty / JS page)."""
import asyncio, html, json, re, sys, unicodedata
from pathlib import Path
import httpx, yaml

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 (compatible; commercial-friendly-apis quote verifier)"}

def norm(t):
    t = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = html.unescape(t)
    t = unicodedata.normalize("NFKC", t)
    t = t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    t = re.sub(r"[‐-―]", "-", t)
    t = re.sub(r"\s+", " ", t).strip().casefold()
    return t

async def main(ids):
    files = [ROOT / "data" / "apis" / f"{i}.yaml" for i in ids] if ids else sorted((ROOT / "data" / "apis").glob("*.yaml"))
    items = []
    for f in files:
        e = yaml.safe_load(f.read_text(encoding="utf-8"))
        for ev in e.get("evidence", []):
            items.append((e["id"], ev))
    cache, sem = {}, asyncio.Semaphore(10)
    async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers=UA) as c:
        async def page(url):
            if url not in cache:
                async def get():
                    async with sem:
                        try:
                            r = await c.get(url); return norm(r.text) if r.status_code < 400 else None
                        except httpx.HTTPError: return None
                cache[url] = asyncio.ensure_future(get())
            return await cache[url]
        out = []
        for eid, ev in items:
            text = await page(ev["url"])
            q = norm(ev["quote"]).rstrip(".")
            st = "unfetchable" if not text or len(text) < 200 else ("ok" if q in text else "missing")
            out.append((eid, ev["field"], st, ev["url"]))
    bad = [o for o in out if o[2] != "ok"]
    for o in bad: print(*o)
    print(f"{len(out)} quotes: {sum(o[2]=='ok' for o in out)} ok, {sum(o[2]=='missing' for o in out)} missing, {sum(o[2]=='unfetchable' for o in out)} unfetchable")

asyncio.run(main(sys.argv[1:]))
