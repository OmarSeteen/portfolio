# omarseteen.space

The source of my online CV. GitHub Pages serves it as static files.

**Status: early.** The page shows my name, and CI runs the checks below on every push. I add
the CV content, the Arabic page and the editor one story at a time.

## How I built it

- `site/` holds the public website: React, built by Vite. It reads its content from
  `site/cv.json`.
- `admin/` holds a small Flask app that will edit that content. I run it on my laptop and
  never deploy it. It has no login, so it refuses any request from another device.
- `privacy_scan.py` stops a commit that contains a phone number. This repository is public
  and git keeps every pushed version, so the scan runs before the commit exists.

The site loads nothing from other servers. It sets no cookies and runs no analytics.

## Run it

You need Python 3.12 or newer, Node 22 and [uv](https://docs.astral.sh/uv/).

```bash
uv venv
uv pip install --require-hashes -r requirements.txt -r requirements-dev.txt
# activate: .venv\Scripts\activate on Windows, source .venv/bin/activate elsewhere

git config core.hooksPath .githooks      # turns on the privacy scan for your commits

npm --prefix site ci
npm --prefix site run dev                # the site, on http://localhost:5173
python -m admin                          # the admin, on http://127.0.0.1:5001
```

## Check it

```bash
python -m pytest                         # admin and privacy-scan tests
python -m ruff check . && python -m black --check .
python privacy_scan.py

npm --prefix site run lint
npm --prefix site run format:check
npm --prefix site run build
python -m playwright install chromium    # once
python -m pytest tests/e2e -m e2e        # browser tests against the built site
npm --prefix site run lighthouse         # fails under 95 in any category
```

CI runs the same commands. The site deploys when all of them pass.
