# 1618.dev

Small calculators and tools — one committed to GitHub per day.

Live at <https://1618.reg32.dev/> — try any tool there in the browser.

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
- [SIP calculator](tools/sip-calculator/) — maturity value of a monthly SIP, total invested, and estimated returns, with optional annual step-up
- [Currency converter](tools/currency-converter/) — live forex rates between 30+ currencies, from European Central Bank reference rates
- [Tip & bill splitter](tools/tip-bill-splitter/) — tip, grand total, and per-person share for any check, with optional rounding to a clean number
- [Salary take-home](tools/salary-take-home/) — rough net-pay estimate from a gross salary for the US, UK, Canada, Australia, India and Ireland (income tax + main social contributions; not tax advice)

### Health
- [BMI calculator](tools/bmi/) — Body Mass Index from weight and height (metric or imperial)
- [Age calculator](tools/age-calculator/) — exact age in years, months, days; total days, weeks, and months

### Maths
- [Prime factorization](tools/prime-factorization/) — unique prime factors of any integer, with all divisors and divisor sum
- [Quadratic equation solver](tools/quadratic-equation/) — roots (real or complex), discriminant, vertex, axis of symmetry, and factored form of ax²+bx+c=0
- [Roman numeral converter](tools/roman-numeral/) — convert a number to Roman numerals or decode a Roman numeral back to a number (1–3999)
- [Triangle solver](tools/triangle-solver/) — solve any triangle from SSS, SAS, ASA, AAS or SSA inputs (sides, angles, perimeter, area)
- [Unit converter](tools/unit-converter/) — convert length, mass, and volume between metric and imperial units

### Science
- [pH / acid-base calculator](tools/ph-acid-base/) — pH, pOH, [H⁺] and [OH⁻]; pH of strong and weak acids and bases from concentration and Ka / Kb

### Developer
- [JSON formatter](tools/json-formatter/) — beautify, validate, or minify JSON, with a choice of indentation, optional key sorting, and line/column error reporting
- [Base64 encoder / decoder](tools/base64/) — encode text to Base64 or decode it back, with standard or URL-safe alphabet, full UTF-8 support, and tolerant decoding
- [UUID generator](tools/uuid-generator/) — generate random v4, time-ordered v7, or legacy v1 UUIDs in bulk, with uppercase and hyphen-free formatting options

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
