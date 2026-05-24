# 1618.dev — notes for Claude

Static site of small calculators. One tool per folder under `tools/<slug>/`.
The goal is to ship one new tool per day; do not bulk-build the backlog.

## Stack & conventions

- Vanilla HTML / CSS / JS. **No build step, no framework, no bundler.**
- Shared `style.css` at the repo root. Don't add per-tool stylesheets; extend the shared sheet.
- Each tool has exactly two files: `index.html` and `logic.py`.
- `logic.py` is the source of truth for the math. It must run standalone as
  `python3 tools/<slug>/logic.py` and include a small `__main__` sanity check.
- Pyodide loads `logic.py` via `pyodide.FS.writeFile` + `import logic`
  (so the `__main__` block doesn't fire in the browser).
- Test changes with `python3 -m http.server 8000` — `file://` won't work because
  the page fetches `logic.py` over HTTP.

## Adding a new tool

1. `mkdir tools/<slug>/` and write `index.html` + `logic.py`.
   Use any existing tool as a template — they all share the same JS skeleton
   (init/pyCall/calculate).
2. Add a `<li>` to the right category section in root `index.html`.
3. Add a bullet under the right category in `README.md`.
4. Sanity-test the logic: `python3 tools/<slug>/logic.py`.

## Implemented — do NOT re-implement

### Finance
- `compound-interest` — Compound Interest Calculator
- `loan-emi` — Loan EMI Calculator
- `annual-annuity` — Annual Annuity Calculator (save + withdraw modes)
- `monthly-annuity` — Monthly Annuity Calculator (save + withdraw modes)

## Backlog

_(empty — ask the user what to build next)_
