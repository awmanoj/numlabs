# 1618.dev

Small calculators and tools — one committed to GitHub per day.

Pure static site. Each tool's logic is written in Python (`logic.py`) and runs in the browser via [Pyodide](https://pyodide.org). No server, no build step.

## Structure

```
.
├── index.html              # home page / gallery
├── style.css               # shared styling
└── tools/
    └── <tool-slug>/
        ├── index.html      # UI
        └── logic.py        # pure-Python logic
```

## Tools

### Finance
- [Compound interest](tools/compound-interest/) — future value of a sum that earns interest on its interest
- [Loan EMI](tools/loan-emi/) — monthly installment + amortization for a fixed-rate loan
- [Annual annuity](tools/annual-annuity/) — yearly save (→ future value) or withdraw (→ annual payout)
- [Monthly annuity](tools/monthly-annuity/) — monthly save (→ future value) or withdraw (→ monthly payout)

## Run locally

Each tool fetches its `logic.py` over HTTP, so `file://` will not work. Serve the repo with anything that returns static files. Easiest:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000>.

## Deploy

The repo is a static site. Enable GitHub Pages on the `main` branch, root folder, and it works as-is.

For the custom domain `1618.dev`, add a `CNAME` file at the repo root containing `1618.dev`, then point the domain's DNS at GitHub Pages.

## Why Python in the browser?

Because the math is interesting, the UI is incidental. Writing the logic in plain Python keeps each `logic.py` runnable and testable on its own (`python3 logic.py`), and the browser just calls into it.
# numlabs
