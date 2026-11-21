#!/usr/bin/env python3
"""Parse both upstream READMEs (pinned snapshots in data/sources/) into normalized,
deduplicated stub entries in data/apis/<id>.yaml. All terms fields start as `unknown`."""
import json, re, sys, collections
from pathlib import Path
from urllib.parse import urlsplit
import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "sources"
OUT = ROOT / "data" / "apis"
REPORT = ROOT / "data" / "import_report.json"

LISTS = {"public-apis": "public-apis.README.md", "public-api-lists": "public-api-lists.README.md"}
LINK = re.compile(r"^\[(?P<name>.+?)\]\(\s*(?P<url>[^)\s]+)\s*\)\s*$")
SHARED_HOSTS = ("github.io", "netlify.app", "herokuapp.com", "vercel.app", "pages.dev", "glitch.me",
                "repl.co", "azurewebsites.net", "appspot.com", "web.app", "firebaseapp.com", "github.com",
                "gitlab.com", "rapidapi.com", "postman.com", "apify.com", "fly.dev", "onrender.com")

def split_row(line):
    line = line.strip()
    if line.startswith("|"): line = line[1:]
    if line.endswith("|"): line = line[:-1]
    cells = re.split(r"(?<!\\)\|", line)
    cells = [c.strip().replace("\\|", "|") for c in cells]
    while len(cells) > 5 and cells[-1] == "":
        cells.pop()
    return cells

def norm_auth(v):
    v = v.strip().strip("`").strip().lower()
    if v in ("no", "none", ""): return "none"
    if v == "apikey": return "apiKey"
    if v.startswith("oauth"): return "OAuth"
    if v == "unknown": return "unknown"
    return "other"

def yn(v):
    v = v.strip().lower()
    return {"yes": "yes", "no": "no"}.get(v, "unknown")

def norm_url(u):
    s = urlsplit(u.strip())
    host = (s.hostname or "").lower()
    if host.startswith("www."): host = host[4:]
    path = s.path.rstrip("/")
    return host, path

def key_for(u):
    host, path = norm_url(u)
    if any(host == h or host.endswith("." + h) for h in SHARED_HOSTS):
        return host + path
    return host if path in ("", "/") else host + path

def clean_url(u):
    # drop tracking params only
    s = urlsplit(u)
    q = "&".join(p for p in s.query.split("&") if p and not p.lower().startswith(("utm_", "ref=", "source=")))
    return s._replace(query=q, fragment="" if not s.fragment.startswith("/") else s.fragment).geturl()

def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower().replace("&", " and ")).strip("-")
    return s or "api"

def parse(list_id, fname, stats):
    rows, cat, cols = [], None, None
    in_index = False
    for line in (SRC / fname).read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            cat, cols = None, None
            continue
        m = re.match(r"^### (.+?)\s*$", line)
        if m:
            title = re.sub(r"^[^\w&]+\s*", "", m.group(1)).strip()
            skip = ("Sponsors" in m.group(1)) or title.startswith("APIs Covered")
            cat, cols = (None if skip else title), None
            continue
        if cat is None or "|" not in line:
            continue
        cells = split_row(line)
        low = [c.lower() for c in cells]
        if low and low[0] in ("api", "name") and "description" in low:
            cols = low; continue
        if re.fullmatch(r"[:\- |]*", line.strip()): continue
        if cols is None:
            stats["skipped_no_header"] += 1; continue
        stats["rows_seen"] += 1
        if len(cells) < 5 or cols[2:5] != ["auth", "https", "cors"]:
            stats["skipped_other_shape"] += 1; stats["shape_samples"].append(line[:120]); continue
        lm = LINK.match(cells[0])
        if not lm:
            stats["skipped_no_link"] += 1; stats["shape_samples"].append(line[:120]); continue
        rows.append(dict(list=list_id, category=cat, name=lm["name"].strip(), url=lm["url"],
                         description=cells[1].strip(), auth=norm_auth(cells[2]),
                         https=(yn(cells[3]) == "yes") if yn(cells[3]) != "unknown" else "unknown",
                         cors=yn(cells[4])))
    return rows

def main():
    all_rows, per_list = [], {}
    for lid, fname in LISTS.items():
        st = collections.Counter(); st["shape_samples"] = []
        r = parse(lid, fname, st); per_list[lid] = {"parsed": len(r), **{k: v for k, v in st.items()}}
        all_rows += r
    # dedup
    groups = collections.OrderedDict()
    for r in all_rows:
        k = key_for(r["url"])
        groups.setdefault(k, []).append(r)
    # secondary: same host+normalized name (different paths)
    name_idx, merged = {}, collections.OrderedDict()
    for k, rs in groups.items():
        host = norm_url(rs[0]["url"])[0]
        nk = (host, re.sub(r"[^a-z0-9]", "", rs[0]["name"].lower()))
        if nk in name_idx and not any(host.endswith(h) for h in SHARED_HOSTS):
            merged[name_idx[nk]] += rs
        else:
            name_idx[nk] = k; merged[k] = list(rs)
    # report same-domain-different-name for human review
    by_host = collections.defaultdict(list)
    for k, rs in merged.items():
        h = norm_url(rs[0]["url"])[0]
        if not any(h.endswith(s) for s in SHARED_HOSTS): by_host[h].append(rs[0]["name"])
    same_domain = {h: n for h, n in by_host.items() if len(n) > 1}

    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("*.yaml"): f.unlink()
    used, entries = set(), []
    for k, rs in merged.items():
        first = rs[0]
        base = slug(first["name"]); eid = base
        if eid in used:
            eid = slug(f"{first['name']} {norm_url(first['url'])[0].split('.')[0]}")
        n = 2
        while eid in used: eid, n = f"{base}-{n}", n + 1
        used.add(eid)
        desc = next((r["description"] for r in rs if r["list"] == "public-apis"), first["description"])
        e = {
            "id": eid, "name": first["name"], "url": clean_url(first["url"]), "category": first["category"],
            "description": desc, "description_source": "upstream",
            "auth": first["auth"], "https": first["https"], "cors": first["cors"],
            "sources": [{"list": r["list"], "name": r["name"], "url": r["url"], "category": r["category"]} for r in rs],
            "link_status": "unchecked",
            "data_license": "unknown", "commercial_use": "unknown", "storage_caching": "unknown",
            "redistribution_display": "unknown", "attribution_required": "unknown",
            "bulk_download": "unknown", "self_host_option": "unknown",
            "verdict": "unknown", "confidence": "low",
        }
        entries.append(e)
        (OUT / f"{eid}.yaml").write_text(yaml.safe_dump(e, sort_keys=False, allow_unicode=True, width=100), encoding="utf-8")
    both = sum(1 for e in entries if len({s["list"] for s in e["sources"]}) == 2)
    cats = collections.Counter(e["category"] for e in entries)
    rep = {"per_list": per_list, "total_rows": len(all_rows), "unique_entries": len(entries),
           "duplicates_removed": len(all_rows) - len(entries), "in_both_lists": both,
           "same_domain_different_name": same_domain, "categories": cats.most_common()}
    REPORT.write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in rep.items() if k not in ("same_domain_different_name", "categories")}, indent=1)[:3000])
    print("same-domain candidates:", len(same_domain))

if __name__ == "__main__":
    main()
