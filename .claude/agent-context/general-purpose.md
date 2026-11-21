# Context: terms-verifier (general-purpose agent, commercial-friendly-apis)

## Project
Curated catalog of public APIs whose data can be used on a commercial site (ads, affiliate links,
stored and displayed on own pages). One YAML per API in `data/apis/<id>.yaml`, schema in
`schema/api.schema.json`, checker `.venv/bin/python scripts/validate.py`. Repo content is English; talk to Max in Russian.
Read `docs/brief.md` sections 3-4 first.

## Your job
For each API id in your brief: open the real terms pages in THIS session (WebFetch; if the page is
JS-rendered or empty, Playwright), fill the terms fields in the YAML, and run validate.py.

## Hard rules
1. Never fill a field from memory. No page opened = `unknown`.
2. Every non-`unknown` terms field needs an `evidence` entry: field, url, quote, checked_at.
   Quote = exact sentence copied from the page, <= 25 words. WebFetch output is summarised by a model:
   if you did not see the exact wording, do not put it in quotes; use `unknown` or re-read via Playwright.
3. Two levels: `data_license` (SPDX id, e.g. CC-BY-4.0) vs `api_terms_url` conditions. They often differ.
4. A site with ads or affiliate links is commercial use. Judge that scenario only.
5. Conflicting or vague terms = `ambiguous` + explanation in `notes`. Terms behind login/PDF you cannot read = `unknown` + note.
6. Check the right scope: free tier vs paid (`commercial_use_scope`), hosted API vs self-hosted.
7. If the URL is dead/redirects elsewhere, follow the redirect, record it in `notes`; if the service is gone set `link_status: dead`, verdict `unknown`.
8. Set `checked_at` (today), `checked_by` (your model name), `confidence`.

## Verdict rules (set `verdict`, do not improvise)
- green: commercial_use=yes AND storage_caching in (yes) AND redistribution_display=yes (attribution allowed).
- yellow: allowed with substantial conditions: paid plan (`paid-only`), self-host only, `limited` caching, share-alike, mandatory logo/link beyond plain credit.
- red: commercial_use=no, or display/storage forbidden.
- unknown: core fields unconfirmed. Any `ambiguous` core field = at best yellow; say why in notes.

## Output
Edit only your assigned YAML files. Return a short table: id, verdict, one-line reason, any doubt. Do not commit.

## Lessons from the pilot (apply to every batch)
- Read exact wording with `curl -sL -A "Mozilla/5.0" <url> | sed 's/<[^>]*>/ /g' | tr -s ' \n' ' '` (WebFetch output is paraphrased; never quote from it). Put scratch files in your own temp dir, not in the repo.
- Playwright is ONE browser shared by all parallel agents: use it only when curl returns an empty shell/JS page, always re-check the URL you landed on, and say in notes if you used it.
- One quote may back several fields only if it explicitly covers them (e.g. "public domain" covers storage/display/share-alike=no). A "free for non-commercial use" sentence does not tell you about caching: leave that field `unknown`.
- Find the API's OWN terms (developer ToS / API policy / licence page), not only the marketing page or a GitHub docs repo. Say in notes which pages you read; if only a pricing page was read, confidence is `low`.
- Check free vs paid scope and hosted vs self-hosted. If a free tier is non-commercial but a paid plan allows it, `commercial_use: paid-only` (verdict yellow).
- Per-provider families (many entries from one vendor): read the vendor's shared terms once, but cite it in each file.
- If upstream `auth` is stale (e.g. now needs a key), fix `auth` and mention it in notes.
- Entries with `link_status: dead` are not in your batch. If the page of a live entry shows the service is shut down, set `link_status: dead`, leave terms `unknown`.
- `verdict` must equal `scripts/verdict.py` output; run validate.py before returning.
- Do not modify files outside your assigned ids. Do not commit.

## Lessons from wave 1
- Playwright is shared: never rely on a plain `navigate`; open a fresh page/context (`browser.newContext()` or a new tab) for each read and re-check the landed URL.
- Use your own scratch dir (e.g. `mktemp -d`), never a fixed shared path like /tmp/s.
- Portals/catalogs: record the portal-wide default licence AND note in `notes` that per-dataset licences may differ; set `confidence: medium` at most. Do not give green from a portal default if the page itself says datasets set their own terms and you did not read any dataset-level licence.
- When a CC BY / CC0 / OGL licence text applies, cite the licence deed for storage/display/attribution only together with the portal's statement that this licence applies.
- Sites blocking curl AND the browser (403/Cloudflare): leave `unknown`, note it, do not try to bypass.
- Free-text `data_license` is fine, but it needs an evidence entry like any other field.

## Second pass (adversarial re-check)
Different job: you get entries already verified once. Your attitude: find reasons why this API CANNOT be used on a commercial site (ads, affiliate links, storing and showing the data).
- Do NOT edit data/apis/*.yaml. Write one JSON file data/second_pass/result-<queue number>.json: a list of objects
  {"id","outcome":"confirmed"|"disputed","reasons":[...short...],"counter_evidence":[{"url","quote"(<=25 words, exact),"field"}],"suggested":{"commercial_use"?, "storage_caching"?, "redistribution_display"?, "attribution_required"?},"note"}.
- Re-open the first-pass evidence URLs AND look for what the first pass did not read: the service's own ToS/AUP/privacy/pricing/developer terms, upstream data-source licences (aggregators), clauses on ads, scraping, caching, resale, "personal use", API-key plan limits, conflicting pages, and whether the service still exists.
- `confirmed` only if you actively looked for blockers and found none. `disputed` if you found a real blocker, a conflict between pages, an unread upstream licence that is demonstrably stricter, or the first-pass quote does not say what was claimed. Quote the blocker.
- Pages blocked for curl: use Playwright in a fresh context; sites blocking everything: say so, outcome `confirmed` is NOT allowed then, use `disputed` with reason "could not re-verify".
- Use your own scratch dir.
