# Contributing

Every verdict must be provable. A pull request that sets a terms field without evidence will fail CI.

## Add or update an API

1. Create or edit `data/apis/<id>.yaml` (id = lowercase slug, equal to the file name). Schema: `schema/api.schema.json`.
2. Open the real terms page and fill: `commercial_use`, `storage_caching`, `redistribution_display`, `attribution_required`, `share_alike`, `data_license`.
3. For **every** field that is not `unknown`, add an `evidence` entry:
   ```yaml
   evidence:
     - field: commercial_use
       url: https://example.com/terms
       quote: "Exact sentence from the page, 25 words at most."
       checked_at: 2026-11-21
   ```
4. Keep the two levels apart: the licence of the **data** vs the **API terms** (a free endpoint may be non-commercial even when the data is CC BY).
5. Judge one scenario: a public site with ads and affiliate links that stores and shows the data.
6. Don't know? Use `unknown`. Contradictory terms? Use `ambiguous` and explain in `notes`.
7. `verdict` is computed from the fields (`scripts/verdict.py`). If it must differ, set `verdict_override` and `override_reason`.

## Check locally

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/validate.py
.venv/bin/python scripts/verify_quotes.py <id>
.venv/bin/python scripts/build.py
```

`README.md`, `categories/` and `dist/` are generated. Never edit them by hand; commit the output of `build.py`.

Not legal advice: this catalog records what the terms say, not how a court would read them.
