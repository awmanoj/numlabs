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
- `pomodoro-timer` — Pomodoro Timer (focus/short-break/long-break phase machine; customizable focus/short/long minutes + rounds-before-long-break; logic.py owns the math — `normalize_config` clamps inputs, `next_state` is the phase machine [long break every Nth focus sprint, breaks always return to focus], `duration_seconds`, `cycle_plan` totals, `format_time` MM:SS. JS owns the clock and sound: countdown driven off a `performance.now()` deadline so background tabs don't drift; Start/Pause/Reset/Skip; round dots; live cycle-time summary; document.title shows the running countdown. Soothing end-of-session chime is generated with the Web Audio API — no audio file — a soft bell arpeggio (major triad + octave), rising at the end of a break, falling at the end of focus; sound toggle + test button; AudioContext resumed on first user gesture)

### Maths
- `golden-ratio` — Golden Ratio Calculator (φ = (1+√5)/2). Four-mode calculator in one `_DISPATCH`-free set of functions: `counterpart(n)` (larger n·φ, smaller n/φ, golden cut of n into long/short parts summing to n), `compare(a,b)` (larger/smaller ratio vs φ, percent error + closeness verdict), `rectangle(width)` (both golden orientations — portrait width·φ and landscape width/φ — each with area + diagonal), `body_check(height, navel)` (height/navel vs φ, navel height for an exact φ). Plus `fibonacci_ratios(k)` (successive F(n+1)/F(n) converging on φ, signed error) and `phi_digits(places)` (φ to ≤2000 dp, exact via `math.isqrt`, truncated not rounded). Static sections: inline-SVG golden spiral (nested golden rectangles + connected quarter-circle arcs), φ-in-nature notes (with a skeptic caveat), face/body "divine proportion" explainer. Live Fibonacci table + decimal-place chips; verdict bands at 0.5/2/5% error
- `mandelbrot` — Mandelbrot Set Explorer (first of a planned fractal series). Interactive escape-time fractal on a `<canvas>`. **Math/render split** (per the user's call): `logic.py` is the source of truth — `escape(cx,cy,max_iter,bailout)` returns escaped/iterations/smooth-μ/final-z, `escape_count`, `orbit` (first N z-values, stops past bailout), `in_main_cardioid`/`in_period2_bulb` interior tests, `classify` (friendly verdict + region) — with a `__main__` that sanity-checks and prints an ASCII portrait. The hot pixel loop is **reimplemented in JS** (`smoothEscape`) because pushing 300k px/frame through Pyodide is too slow; Pyodide loads in the background and is called **only** for the point inspector so logic.py is genuinely used in-browser. UI: drag-pan / wheel-zoom-toward-cursor / dblclick-zoom / single-click-inspect via Pointer events; low-res preview (step=3) during interaction + debounced full render; smooth-μ colouring through IQ cosine palettes (5 presets); famous-location chips (Seahorse/Elephant Valley, Triple Spiral, Mini-Mandelbrot, Tendrils) that also set max-iter; iteration slider, Save-PNG, info bar (centre/span/zoom×); overlay `<canvas>` draws the c-marker + orbit polyline. Planned siblings: Julia set, Newton fractal, Barnsley fern, Sierpinski triangle, Koch snowflake.
- `julia` — Julia Set Explorer (2nd in the fractal series; sibling to `mandelbrot`, reuses its scaffold). Same `z→z²+c` iteration but fixes c and sweeps the start z. **Signature interaction:** a mini-Mandelbrot c-picker canvas — drag the dot across it and the Julia set re-renders live (the Mandelbrot set is the map of all Julia sets). `logic.py` is source of truth: `escape(zr,zi,cr,ci,…)` (now z and c are separate args), `escape_count`, `orbit`, plus `mandel_escape_count`/`is_connected`/`describe_c` for the Fatou–Julia connectivity dichotomy (c in M → connected; c outside → dust), and `classify`; `__main__` sanity-checks (c=0 → unit-disc filled Julia) and prints an ASCII Douady rabbit. Same JS render split as `mandelbrot` (hot loop `juliaSmoothEscape` in JS; Pyodide only for the inspector). UI extras over Mandelbrot: live connected/dust badge, famous-c chips (Douady rabbit, San Marco, Dendrite, Siegel disk, Spiral, Dragon), "Random c" that samples near the M boundary. Shares the `.fractal-stage`/`.fractal-bar`/`.controls-grid` CSS.
- `newton-fractal` — Newton Fractal Explorer (3rd in the fractal series; **escape-time → root-finding**, genuinely different math). Newton's method `z → z − a·p(z)/p′(z)` on the complex plane, each start coloured by *which* root it converges to, brightness by speed; black = never settles (cycle/edge). `logic.py` is source of truth: `POLYS` (5 polynomials as descending-power coeff lists + cached roots), `_polyval`/`_deriv` (Horner, Python `complex`), `newton(zr,zi,poly,max_iter,tol,a)` → converged/root_index/iterations, `orbit`, `classify`, `roots_of`; `__main__` checks each cached root really is a root, that z=0 on `z³−2z+2` never converges (the 0→1→0 cycle trap), and prints an ASCII basin map. JS mirrors POLYS (literal coeffs+roots so first paint needs no Pyodide) and runs the Horner Newton hot loop; Pyodide only for the inspector. UI over the escape-time tools: polynomial select (z³−1, z⁴−1, z⁵−1, z³−2z+2 "the trap", z⁸+15z⁴−16), **relaxation-a slider** (0.3–1.9, the signature play knob), 3 per-root colour schemes (HSL hue per root × speed-shaded lightness), root markers on the overlay. Shares `.fractal-stage`/`.fractal-bar`/`.controls-grid` CSS.
- `barnsley-fern` — Barnsley Fern Generator (4th in the fractal series; **IFS / chaos game** — a third family, neither escape-time nor root-finding). Plots an Iterated Function System's attractor by the chaos game: from a point, repeatedly pick one of 4 affine maps by probability and jump, plotting each landing. `logic.py` is source of truth: `PRESETS` (4 ferns — classic/cyclosorus/fishbone/windswept — each 4 maps as `{a,b,c,d,e,f,p}`), `apply_map`, `normalize` (renormalize p→1), `choose`/`step` (chaos-game step), `run`/`bounds` (point gen + bbox, seeded `random.Random` for determinism), and `describe_map` (linear-part decomposition: determinant, singular values s_max/s_min, polar-rotation angle, contractive?). `__main__` checks probability bins, classic-fern bbox, that all maps contract, and prints an ASCII fern. JS mirrors PRESETS and runs the chaos-game hot loop; **Pyodide genuinely backs the on-page map-geometry table** (calls `describe_map` per map). UI is different from the escape-time tools: **progressive animation** (accumulates ~200k points into a persistent ImageData over rAF batches — you watch the fern draw itself), an **editable 4×7 affine-coefficient table** (edit any a..f/p → fern re-fits + redraws, marks preset "custom"), preset chips, botanical/by-transform colour, points slider, replay, pan/zoom (re-runs the game into the new view). Shares `.fractal-stage`/`.fractal-bar`/`.controls-grid` CSS plus new `.coeff-table`/`.coeff-input`.
- `prime-factorization` — Prime Factorization (factors, all divisors, divisor count + sum)
- `quadratic-equation` — Quadratic Equation Solver (roots real/complex, discriminant, vertex, axis of symmetry, Vieta sum/product, rational factored form)
- `roman-numeral` — Roman Numeral Converter (number ↔ Roman, 1–3999)
- `triangle-solver` — Triangle Solver (SSS, SAS, ASA, AAS, SSA — law of cosines / law of sines; ambiguous case handled)
- `unit-converter` — Unit Converter (length, mass, volume; metric ↔ imperial via exact base-unit factors)

### Science
- `ph-acid-base` — pH / acid-base calculator (pH ↔ pOH ↔ [H⁺] ↔ [OH⁻]; strong/weak acid/base pH from concentration and Ka/Kb)
- `speed-distance-time` — Speed / distance / time calculator (give any two, solve the third via distance = speed × time; converts each quantity through SI base units — m, s, m/s — so mixed units work, then reports the answer in every supported unit; distance mm/cm/m/km/in/ft/yd/mi/nmi, speed m/s/km/h/mph/ft/s/knot, time s/min/h/day; rejects zero divisor and same-quantity/target-collision inputs; treats velocity as plain average speed, no direction)

### Developer
- `json-formatter` — JSON Formatter / Validator (beautify with 2/4-space or tab indent, minify, optional sort-keys; line/column error reporting; UTF-8 preserved; stats: lines/bytes/values/depth)
- `base64` — Base64 Encoder / Decoder (encode text → Base64 or decode back; standard and URL-safe alphabets; UTF-8 round-trip; tolerant decoding — strips whitespace, restores padding, accepts either alphabet; stats: input/output bytes, output chars)
- `uuid-generator` — UUID Generator (v4 random, v7 time-ordered, v1 time+node, nil; bulk generation up to 1000; uppercase and hyphen-free formatting options; v7 assembled by hand per RFC 9562 since stdlib has no uuid7; secrets-backed randomness)

## Backlog

**Fractal series (Maths)** — agreed lineup, build one at a time, not in bulk.
Mandelbrot + Julia + Newton + Barnsley fern shipped; remaining, roughly in order:
- `sierpinski-triangle` — chaos game vs. recursive subdivision (two routes, one
  fractal)
- `koch-snowflake` — recursive edge replacement / L-system; infinite perimeter,
  finite area

Same math/render split as `mandelbrot`: logic.py owns the real math + a `__main__`
sanity check, JS owns the hot render loop.
