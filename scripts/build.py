#!/usr/bin/env python3
"""Generate README.md, categories/*.md and dist/apis.json from data/apis/*.yaml.
Never edit generated files by hand. `build.py --check` exits 1 if they are stale (for CI)."""
import json, re, sys, collections, datetime
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
ICON = {"green": "🟢", "yellow": "🟡", "red": "🔴", "unknown": "⚪"}
YN = {"yes": "✅", "no": "❌", "limited": "⚠️ limited", "paid-only": "💲 paid", "ambiguous": "❓ ambiguous",
      "unknown": "—"}
ATTR = {"yes": "required", "no": "not required", "ambiguous": "❓ unclear", "unknown": "—"}
SNAP = {"public-apis": "867085ccdf4adb7166bdac207b82f117bb418eb0", "public-api-lists": "6491e2fb2bc32dc7955b95ef6f64001d1b0db764"}

def esc(s): return str(s).replace("|", "\\|").replace("\n", " ").strip()
def slug(c): return re.sub(r"[^a-z0-9]+", "-", c.lower()).strip("-")

def load():
    return sorted((yaml.safe_load(f.read_text(encoding="utf-8")) for f in (ROOT / "data" / "apis").glob("*.yaml")),
                  key=lambda e: e["name"].lower())

def vicon(e):
    return ICON[e["verdict"]] + (" ⚠️" if e.get("license_scope") == "portal-default" else "")

def terms_url(e):
    if e.get("api_terms_url"): return e["api_terms_url"]
    ev = [i["url"] for i in e.get("evidence", [])]
    return ev[0] if ev else ""

def row(e, full=True):
    name = f"[{esc(e['name'])}]({e['url']})"
    if e.get("link_status") == "dead": name += " 🔗†"
    t = terms_url(e)
    cells = [name, esc(e.get("description", ""))[:140].rstrip(), vicon(e), YN.get(e["commercial_use"], "—"),
             YN.get(e["storage_caching"], "—"), ATTR.get(e.get("attribution_required", "unknown"), "—"),
             f"[terms]({t})" if t else "—", e.get("checked_at", "—")]
    return "| " + " | ".join(cells) + " |"

HEAD = "| API | Description | Verdict | Commercial use | Storage | Attribution | Terms | Checked |\n|---|---|---|---|---|---|---|---|"

def build():
    ALL = load()
    E = [e for e in ALL if e.get("applicable") is not False]
    n_na = len(ALL) - len(E)
    today = max([e.get("checked_at", "") for e in E] + [""]) or "n/a"
    cnt = collections.Counter(e["verdict"] for e in E)
    checked = sum(1 for e in E if e.get("checked_at"))
    bycat = collections.defaultdict(list)
    for e in E: bycat[e["category"]].append(e)
    out = {}
    # categories
    for c, es in bycat.items():
        cc = collections.Counter(e["verdict"] for e in es)
        lines = [f"# {c}", "", f"> Generated file. {len(es)} APIs: 🟢 {cc['green']} · 🟡 {cc['yellow']} · 🔴 {cc['red']} · ⚪ {cc['unknown']}. "
                 "[Back to README](../README.md)", "", HEAD]
        order = {"green": 0, "yellow": 1, "red": 2, "unknown": 3}
        lines += [row(e) for e in sorted(es, key=lambda e: (order[e["verdict"]], e["name"].lower()))]
        lines += ["", "† = link did not respond when last checked."]
        out[f"categories/{slug(c)}.md"] = "\n".join(lines) + "\n"
    green = [e for e in E if e["verdict"] == "green"]
    r = [
        "# Commercial-friendly APIs", "",
        "Public API lists tell you whether an API needs a key, HTTPS or CORS. They don't tell you whether you may put its data "
        "on a site with ads or affiliate links, store it, or show it on your own pages. This catalog does, with proof: "
        "every verdict links to the terms page and quotes the clause it rests on.", "",
        "> ⚠️ **Not legal advice.** Terms change. Always re-read the linked terms before you ship.", "",
        f"**{len(E)}** APIs listed ({n_na} more kept for reference as not applicable) · **{checked}** checked · 🟢 {cnt['green']} · 🟡 {cnt['yellow']} · 🔴 {cnt['red']} · "
        f"⚪ {cnt['unknown']} · last check: {today}", "",
        "## Legend", "",
        "| | Meaning |", "|---|---|",
        "| 🟢 | Commercial use, storage and display are allowed (attribution may be required) |",
        "| 🟡 | Allowed with real conditions: paid plan, self-hosting, limited caching, share-alike, or unclear terms |",
        "| 🔴 | Not suitable for a commercial site |",
        "| ⚪ | Not checked yet, or terms could not be confirmed |",
        "| ⚠️ | The licence is the portal's default; individual datasets may carry other terms |", "",
        "Scenario judged: a public website with ads and affiliate links that stores and republishes API data. "
        "Data licence and API terms are tracked separately because they often differ. Fields: `commercial_use`, `storage_caching`, "
        "`redistribution_display`, `attribution_required`, `share_alike`, each with evidence (URL, quote, date) in `data/apis/<id>.yaml`.", "",
        "## 🟢 Commercial-friendly", ""]
    r += [HEAD] + [row(e) for e in green] if green else ["_None checked yet._"]
    r += ["", "## Categories", "", "| Category | APIs | 🟢 | 🟡 | 🔴 | ⚪ |", "|---|---|---|---|---|---|"]
    for c in sorted(bycat):
        cc = collections.Counter(e["verdict"] for e in bycat[c])
        r.append(f"| [{c}](categories/{slug(c)}.md) | {len(bycat[c])} | {cc['green']} | {cc['yellow']} | {cc['red']} | {cc['unknown']} |")
    r += ["", "## Data", "",
          "Machine-readable dataset: [`dist/apis.json`](dist/apis.json) (built from `data/apis/*.yaml`, one file per API). "
          "README and category pages are generated by `scripts/build.py` and must not be edited by hand. See [CONTRIBUTING.md](CONTRIBUTING.md).", "",
          "## Sources & attribution", "",
          "API names, URLs and descriptions were imported from two MIT-licensed lists (full notices in [NOTICE](NOTICE)):",
          f"- [public-apis/public-apis](https://github.com/public-apis/public-apis) @ `{SNAP['public-apis'][:7]}`",
          f"- [public-api-lists/public-api-lists](https://github.com/public-api-lists/public-api-lists) @ `{SNAP['public-api-lists'][:7]}`", "",
          "## License", "", "Code: MIT ([LICENSE](LICENSE)). Data (the YAML records and the verdicts): CC BY 4.0 ([LICENSE-DATA](LICENSE-DATA)). Descriptions imported from the two source lists stay under their MIT notices ([NOTICE](NOTICE)).", ""]
    out["README.md"] = "\n".join(r)
    out["dist/apis.json"] = json.dumps({"generated_for": today, "count": len(ALL), "apis": ALL}, indent=1, ensure_ascii=False,
                                       default=str) + "\n"
    return out

def main():
    out = build()
    if "--check" in sys.argv:
        stale = [p for p, t in out.items() if not (ROOT / p).exists() or (ROOT / p).read_text(encoding="utf-8") != t]
        cat = ROOT / "categories"
        stale += [f"categories/{f.name}" for f in cat.glob("*.md") if f"categories/{f.name}" not in out] if cat.exists() else []
        print("stale:", stale or "none"); sys.exit(1 if stale else 0)
    (ROOT / "categories").mkdir(exist_ok=True); (ROOT / "dist").mkdir(exist_ok=True)
    for f in (ROOT / "categories").glob("*.md"): f.unlink()
    for p, t in out.items(): (ROOT / p).write_text(t, encoding="utf-8")
    print(f"wrote {len(out)} files")

main()
