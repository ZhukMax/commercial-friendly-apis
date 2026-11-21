#!/usr/bin/env python3
"""One-off maintainer decisions: portal-default scope, not-applicable entries, duplicate merge. Idempotent."""
import glob, re, sys
from pathlib import Path
import yaml
sys.path.insert(0, str(Path(__file__).resolve().parent))
from verdict import compute

ROOT = Path(__file__).resolve().parent.parent
def path(i): return ROOT / "data/apis" / f"{i}.yaml"
def load(i): return yaml.safe_load(path(i).read_text(encoding="utf-8"))
def save(e): path(e["id"]).write_text(yaml.safe_dump(e, sort_keys=False, allow_unicode=True, width=100), encoding="utf-8")
E = {Path(f).stem: yaml.safe_load(open(f)) for f in glob.glob(str(ROOT / "data/apis/*.yaml"))}

# 1) duplicates: (primary, secondary)
PAIRS = [("nasdaq-data-link", "quandl"), ("graphhopper", "graphhopper-graphhopper"), ("stormglass", "storm-glass"),
         ("polygon", "polygon-io"), ("newton", "newton-newton"), ("spacex", "spacex-api"), ("binance", "binance-github"),
         ("bclaws", "bclaws-bclaws"), ("transport-for-united-states-nextbus", "transport-for-united-states"),
         ("gbif", "gbif-api"), ("blockchain", "blockchain-blockchain"), ("ipapi-co", "ipapi-co-ip-location"),
         ("jobspipe", "jobspipe-jobspipe"), ("mexc", "mexc-global"), ("us-autocomplete", "us-autocomplete-smartystreets"),
         ("us-extract", "us-extract-smartystreets"), ("us-street-address", "us-street-address-smartystreets"),
         ("us-zipcode", "us-zipcode-smartystreets"), ("iqair", "airvisual"), ("zornade", "zornade-zornade"),
         ("mapbox", "mapbox-mapbox"), ("nager-date", "nager-date-nagerholidays"), ("filingrail", "filingrail-filingrail")]
SEV = {"red": 0, "yellow": 1, "unknown": 2, "green": 3}
merged = []
for a, b in PAIRS:
    if a not in E or b not in E or not path(b).exists(): continue
    pa, pb = E[a], E[b]
    # primary: the one with more evidence; ties keep the listed primary
    if len(pb.get("evidence", [])) > len(pa.get("evidence", [])) + 2: pa, pb = pb, pa
    seen = {(x["list"], x["url"]) for x in pa["sources"]}
    pa["sources"] += [x for x in pb["sources"] if (x["list"], x["url"]) not in seen]
    have = {(x["field"], x["quote"]) for x in pa.get("evidence", [])}
    pa.setdefault("evidence", []).extend(x for x in pb.get("evidence", []) if (x["field"], x["quote"]) not in have)
    pa["aliases"] = sorted(set(pa.get("aliases", [])) | {pb["id"]} | set(pb.get("aliases", [])))
    note = f"Merged duplicate entry `{pb['id']}`."
    pa["notes"] = (pa.get("notes", "") + " " + note).strip()
    if pa.get("checked_at") and pb.get("checked_at"):
        # never let the merge make the verdict rosier than either record
        worst = min((pa["verdict"], pb["verdict"]), key=lambda v: SEV[v])
        if SEV[worst] < SEV[pa["verdict"]] and worst != "unknown":
            pa["verdict_override"] = worst; pa["override_reason"] = f"Merged with {pb['id']}: more cautious verdict kept."
        pa["verdict"] = compute(pa)
    save(pa); path(pb["id"]).unlink(); merged.append((pa["id"], pb["id"]))
    E.pop(pb["id"], None); E[pa["id"]] = pa

# 2) portal-default scope
KW = ("per-dataset", "per dataset", "portal default", "portal-wide", "portal level", "each dataset", "dataset-level",
      "dataset level", "per-record", "per record", "per-indicator", "licence varies per", "license varies per", "varies per dataset")
portal = []
for i, e in E.items():
    if not e.get("checked_at") or e.get("verdict") not in ("green", "yellow"): continue
    blob = " ".join(str(e.get(k, "")) for k in ("notes", "second_check_note", "override_reason", "data_license")).lower()
    if any(k in blob for k in KW) and e["category"] in ("Government", "Open Data", "Geocoding", "Transportation", "Health", "Environment",
                                                         "Science & Math", "Books", "Weather", "Art & Design", "Calendar"):
        if e.get("license_scope") != "portal-default":
            e["license_scope"] = "portal-default"; save(e); portal.append(i)

# 3) not applicable (not a data source)
PHRASES = ("not a data source", "not really a data source", "not a real data source", "not a data api", "not an open data source",
           "not a general data source", "not a free general data source", "not a usable data source")
EXPLICIT = {"klarna", "moov", "mailchimp", "redash", "smartsheet", "metabase", "woocommerce", "google-calendar", "google-analytics", "gmail",
            "trello", "mailgun", "mailjet", "square", "fitbit", "strava", "tredict", "smartcar", "mercadopago", "billplz", "boleto-cloud",
            "ynab", "cryptapi", "cosmos-pay", "coinremitter", "gasrent", "nicehash", "bitpanda", "infura-ethereum", "chainpoint", "verifyum",
            "feedbin", "the-old-reader", "dabloons", "hirelayer", "svg-new", "pic2svg", "upres", "php-noise", "word-cloud", "pickshade",
            "get-started-with-web3", "instatus", "taxid", "chainlink", "srp-energy", "countly", "shields", "github-readme-stats",
            "github-contribution-chart-generator", "attestwire", "temsor", "dummyimage", "postman-echo", "purgomalum", "schemashield",
            "lob-com", "numvalidate", "intellibook", "rappi", "olx-poland", "lazada", "shopee", "flipkart-marketplace", "opentiendas",
            "fast-data-job-search", "siftsmith-company-jobs", "cartola-fc", "outfit-showcase", "apache-superset", "oddsbench", "lucyd",
            "clearbit-logo", "grab", "plaid", "mono", "nubra", "alchemy-ethereum", "swiftnodes", "nownodes", "blazephoenix", "block-lottos",
            "sprytools-email-validation", "kiprio-email-validation", "datascreeniq", "invowerk", "invoicein", "invovate", "stanza-vat-validator",
            "zoho-books", "swiftkanban", "mypayslip-lk", "us-freelancer-tax", "pink-agentic-ai-payments", "face-shape-guide-lookup"}
na = []
for i, e in E.items():
    blob = " ".join(str(e.get(k, "")) for k in ("notes", "second_check_note")).lower()
    if i in EXPLICIT or any(p in blob for p in PHRASES):
        if e.get("applicable") is not False:
            e["applicable"] = False
            e["not_applicable_reason"] = "Not a public data source (payment/e-mail/self-hosted software/account-scoped/demo/utility API); kept for reference."
            save(e); na.append(i)
print("merged", len(merged), merged)
print("portal-default", len(portal)); print("not applicable", len(na))
