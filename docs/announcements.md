# Announcement drafts (English)

Numbers as of 2026-11-21. Not posted anywhere.

## Reddit (r/webdev, r/programming-adjacent communities that allow self-promotion)

**I checked the terms of ~1,300 public APIs for commercial-site use. Only 167 came out green.**

The popular API lists (public-apis, public-api-lists) tell you about auth, HTTPS and CORS. They don't tell you whether you can put the data on a site with ads or affiliate links, store it, or republish it. Their MIT licence covers the list, not the APIs.

So I built a catalogue that records, per API: commercial use, storage/caching, display/redistribution, attribution, share-alike, with the exact clause (URL, quote, date) behind every claim. Anything I couldn't prove stays `unknown`.

Rough results for the ~1,300 I checked: 🟢 167, 🟡 604, 🔴 94, the rest could not be confirmed (many sites block bots or publish no terms). Green entries got a second, adversarial pass ("find reasons this can't be used commercially"); about a third of the first-pass greens did not survive it.

Things I learned: free tiers are often non-commercial while the data licence (e.g. CC BY) is fine; portals publish a default licence but datasets differ; aggregators can't relicense their upstream; plenty of "free" APIs forbid caching.

It's one YAML file per API plus a generated README and JSON (CC BY 4.0). Verdicts are derived from fields by a script, and CI rejects any claim without a quote. Not legal advice. Corrections welcome: https://github.com/ZhukMax/commercial-friendly-apis

## Hacker News (Show HN)

**Show HN: A catalogue of public APIs with verified commercial-use terms**

Existing API lists don't say whether you may use an API's data on a monetised site. I checked ~1,300 APIs against their actual terms pages and recorded commercial use, caching, display and attribution, each with a dated quote from the terms. 167 are green, 604 yellow, 94 red; the remainder is unknown (bot-blocked pages, no published terms).

Method: one agent pass to read the terms, then an adversarial pass on every green and ambiguous entry. Verdicts are computed from fields by a script; CI fails on any claim without a quote. Known limits: portal-level licences (marked ⚠️) can differ per dataset, ~15% of quotes were read through a browser and are not automatically re-verifiable, and terms change.

Data is CC BY 4.0, code MIT, one YAML per API plus dist/apis.json. Not legal advice. https://github.com/ZhukMax/commercial-friendly-apis

## dev.to

**Which public APIs can you actually use on a site with ads? I checked ~1,300**

(Intro: the gap in public-apis lists. Method in four bullets. Three surprises: non-commercial free tiers, portal-default licences, aggregators. A short table of the green categories: government and open-data portals, weather, science, finance statistics, museums. Link to the repo, the schema, and how to contribute. State the limits and "not legal advice" in the first screen, not at the bottom.)
