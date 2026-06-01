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
   (init/pyCall/calculate) **and the same SEO head/footer pattern**.
2. Add a `<li>` to the right category section in root `index.html`.
3. Add a bullet under the right category in `README.md`.
4. Add a `<url>` entry to `sitemap.xml`.
5. Sanity-test the logic: `python3 tools/<slug>/logic.py`.

   Templating from an existing tool carries the analytics snippet along (see
   **Analytics** below) — just confirm it's present in the new `<head>`.

## SEO conventions

Every tool page (`tools/<slug>/index.html`) must include in its `<head>`:

1. **Unique `<title>`** — primary keyword first, brand last. Pattern:
   `"<Tool name> Calculator — <distinguisher> | 1618.dev"`.
2. **`<meta name="description">`** — 140–160 chars. Lead with the value the
   user gets; include the primary keyword once.
3. **`<meta name="keywords">`** — comma-separated search terms. Google
   ignores it, but Bing and on-site search engines still use it; cheap to add.
4. **`<link rel="canonical">`** — absolute `https://1618.dev/...` URL.
5. **Open Graph** (`og:type`, `og:title`, `og:description`, `og:url`,
   `og:site_name`) + **Twitter card** (`twitter:card=summary`, title,
   description) — for social link previews.
6. **JSON-LD `WebApplication` schema** in a
   `<script type="application/ld+json">` block.
   Use `applicationCategory: "FinanceApplication"` for finance tools.

Every tool `<footer>` must include:

- A `.related` nav linking to sibling tools in the same category — internal
  links help crawlers map the site and help users discover.
- A `.keywords` cloud of `<span class="kw">…</span>` pills (8–12 phrases).
  Mix exact-match queries and long-tail variants.
  **Pills must remain visible.** Hidden / cloaked keyword text is a Google
  ranking penalty — never `display:none` them or push them off-screen.

The repo root has `robots.txt` (allows all, points to sitemap) and
`sitemap.xml` (lists every page). **Update `sitemap.xml` when shipping a
new tool**, otherwise it won't be crawled.

## Analytics

Every page (root + every tool) carries the same GA4 gtag.js snippet, placed
right after `<meta charset>` in the `<head>`. Measurement ID: `G-1YEEJCL2E6`.
New tools must include it — it comes for free when you template from an
existing tool, so just confirm it's present:

```html
<meta charset="utf-8" />
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-1YEEJCL2E6"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-1YEEJCL2E6');
</script>
```

## Implemented — do NOT re-implement

### Finance
- `compound-interest` — Compound Interest Calculator
- `loan-emi` — Loan EMI Calculator
- `annual-annuity` — Annual Annuity Calculator (save + withdraw modes)
- `monthly-annuity` — Monthly Annuity Calculator (save + withdraw modes)
- `sip-calculator` — SIP Calculator (monthly investment → maturity value, total invested, estimated returns; beginning-of-month/annuity-due; optional annual step-up)
- `currency-converter` — Currency Converter (live ECB rates via Frankfurter API; 30+ currencies)
- `tip-bill-splitter` — Tip & Bill Splitter (tip, total, per-person share; optional rounding up/nearest/down to a clean increment; currency-agnostic)
- `salary-take-home` — Salary Take-Home Calculator by country (US/UK/CA/AU/IN/IE; headline income-tax bands + main employee social contributions; rough estimate, single filer, heavily disclaimed; data-driven `_DISPATCH` model in logic.py)
- `can-i-afford-it` — "Can I afford it?" calculator (price → hours/days/weeks of work + share of a month's pay; income quoted per hour/week/month/year, annualised via hours-per-week × weeks-per-year; optional take-home % to reckon in net pay; live-update UI, currency-symbol field; perspective tool, not financial advice)
- `coffee-habit-cost` — Coffee habit cost calculator (price per cup × cups/day → per-day/week/month/year totals; days-per-week scales the year via days_per_week/7 × 365, so 7 days = the classic "× 365"; projected spend over N years vs. future value of the same monthly amount invested at a given annual return, compounded monthly, plus the growth portion; live-update UI, currency-symbol field; reality-check tool, not financial advice)
- `freelance-rate` — Freelance rate calculator (works backwards from a salary goal to the hourly rate you must charge; goal + annual business expenses grossed up by tax %, divided by billable hours/year = (52 − weeks_off) working weeks × hours_per_week × billable_pct; derives day rate (billable week ÷ 5), week rate, and monthly revenue needed; verdict bands on billable % flag rosy utilization; clamps weeks_off ≤ 51, tax ≤ 95%; ValueError on zero billable hours; live-update UI, currency-symbol field; pricing floor, not financial advice)

### Health
- `bmi` — BMI (Body Mass Index) Calculator, metric + imperial
- `age-calculator` — Age Calculator (years / months / days / total weeks / total days)

### Everyday Life
- `reading-time` — Reading Time Estimator (paste text → silent reading time and spoken-aloud time at a chosen wpm, plus word / character / chars-without-spaces / sentence / paragraph counts; live update on input; slow/average/fast presets + custom wpm; speaking time at a fixed ~130 wpm pace)

### Maths
- `prime-factorization` — Prime Factorization (factors, all divisors, divisor count + sum)
- `quadratic-equation` — Quadratic Equation Solver (roots real/complex, discriminant, vertex, axis of symmetry, Vieta sum/product, rational factored form)
- `roman-numeral` — Roman Numeral Converter (number ↔ Roman, 1–3999)
- `triangle-solver` — Triangle Solver (SSS, SAS, ASA, AAS, SSA — law of cosines / law of sines; ambiguous case handled)
- `unit-converter` — Unit Converter (length, mass, volume; metric ↔ imperial via exact base-unit factors)

### Science
- `ph-acid-base` — pH / acid-base calculator (pH ↔ pOH ↔ [H⁺] ↔ [OH⁻]; strong/weak acid/base pH from concentration and Ka/Kb)

### Developer
- `json-formatter` — JSON Formatter / Validator (beautify with 2/4-space or tab indent, minify, optional sort-keys; line/column error reporting; UTF-8 preserved; stats: lines/bytes/values/depth)
- `base64` — Base64 Encoder / Decoder (encode text → Base64 or decode back; standard and URL-safe alphabets; UTF-8 round-trip; tolerant decoding — strips whitespace, restores padding, accepts either alphabet; stats: input/output bytes, output chars)
- `uuid-generator` — UUID Generator (v4 random, v7 time-ordered, v1 time+node, nil; bulk generation up to 1000; uppercase and hyphen-free formatting options; v7 assembled by hand per RFC 9562 since stdlib has no uuid7; secrets-backed randomness)

## Backlog

_(empty — ask the user what to build next)_
