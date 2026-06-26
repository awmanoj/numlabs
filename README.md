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
- [Can I afford it?](tools/can-i-afford-it/) — turn any price into hours, days, and weeks of work for what you earn, plus its share of a month's take-home pay
- [Coffee habit cost](tools/coffee-habit-cost/) — what a daily coffee costs per week, month, and year, plus what the same money could grow to if invested instead
- [Days left on Earth](tools/days-left-on-earth/) — how much of your life is spent and how much is left, in days, weeks and summers, drawn as a life-in-weeks grid (each square is one week)
- [Freelance rate](tools/freelance-rate/) — the hourly rate you need to charge to hit a salary goal, after unpaid time off, non-billable hours, business expenses, and tax
- [If I had invested…](tools/if-i-invested/) — what a lump sum in an Indian stock or index (Reliance, TCS, Infosys, HDFC Bank, the Sensex…) at a past year-end would be worth today: growth multiple, total return, and CAGR, dividends reinvested

### Health
- [BMI calculator](tools/bmi/) — Body Mass Index from weight and height (metric or imperial)
- [Age calculator](tools/age-calculator/) — exact age in years, months, days; total days, weeks, and months

### Everyday Life
- [Reading time estimator](tools/reading-time/) — how long any text takes to read silently or speak aloud, with word, character, sentence, and paragraph counts
- [Pomodoro timer](tools/pomodoro-timer/) — focus sprints and breaks with customizable lengths and a soothing, generated chime at the end of each session

### Personality & Fun
- [Birth year fun facts](tools/birth-year-facts/) — what released and happened the year you were born, plus the age you turn this year, your generation, Chinese zodiac, leap year, and Roman numerals

### Maths
- [Golden ratio calculator](tools/golden-ratio/) — phi partners of any number, golden-ratio checks, golden rectangles, the "is your body golden?" test, phi to 1000 decimals, and Fibonacci convergence on 1.618
- [Mandelbrot set explorer](tools/mandelbrot/) — interactive escape-time fractal: drag to pan, scroll to zoom, tune iteration depth and colour palette, jump to famous spots, and click any point to inspect its orbit and escape count
- [Julia set explorer](tools/julia/) — drag the parameter c across a mini Mandelbrot map and watch the Julia fractal morph in real time; connected-vs-dust read-out, famous-c presets, zoom, recolour, and per-point orbit inspector
- [Newton fractal explorer](tools/newton-fractal/) — Newton's-method basins of attraction for z³−1 and other polynomials; colour by which root each point falls to, brightness by speed, a relaxation-factor slider, zoom, and a per-point path inspector
- [Barnsley fern generator](tools/barnsley-fern/) — an Iterated Function System drawn by the chaos game; watch the fern form from four affine maps, edit the coefficients and probabilities to mutate it, switch ferns (Cyclosorus, Fishbone, Windswept), recolour, zoom, with a logic.py-computed map-geometry table
- [Sierpinski triangle generator](tools/sierpinski-triangle/) — one fractal reached two ways: the random chaos game (half-steps to a corner) and deterministic recursive subdivision land on the same gasket; depth slider, live triangle-count (3ⁿ) and area-remaining ((3/4)ⁿ) stats, a Pascal's-triangle-mod-2 third route, zoom, recolour
- [Prime factorization](tools/prime-factorization/) — unique prime factors of any integer, with all divisors and divisor sum
- [Quadratic equation solver](tools/quadratic-equation/) — roots (real or complex), discriminant, vertex, axis of symmetry, and factored form of ax²+bx+c=0
- [Roman numeral converter](tools/roman-numeral/) — convert a number to Roman numerals or decode a Roman numeral back to a number (1–3999)
- [Triangle solver](tools/triangle-solver/) — solve any triangle from SSS, SAS, ASA, AAS or SSA inputs (sides, angles, perimeter, area)
- [Unit converter](tools/unit-converter/) — convert length, mass, and volume between metric and imperial units

### Science
- [pH / acid-base calculator](tools/ph-acid-base/) — pH, pOH, [H⁺] and [OH⁻]; pH of strong and weak acids and bases from concentration and Ka / Kb
- [Speed / distance / time calculator](tools/speed-distance-time/) — give any two of speed, distance and time, get the third, in metric and imperial units
- [Ohm's law calculator](tools/ohms-law/) — give any two of voltage, current, resistance and power, get the other two (V = IR, P = VI), with metric unit prefixes

### Developer
- [JSON formatter](tools/json-formatter/) — beautify, validate, or minify JSON, with a choice of indentation, optional key sorting, and line/column error reporting
- [Base64 encoder / decoder](tools/base64/) — encode text to Base64 or decode it back, with standard or URL-safe alphabet, full UTF-8 support, and tolerant decoding
- [UUID generator](tools/uuid-generator/) — generate random v4, time-ordered v7, or legacy v1 UUIDs in bulk, with uppercase and hyphen-free formatting options
- [Cron expression explainer](tools/cron-expression/) — translate a crontab schedule into plain English, with a field-by-field breakdown and the next run times; supports ranges, steps, lists, month/weekday names, and @daily-style macros

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
