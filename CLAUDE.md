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

### Health
- `bmi` — BMI (Body Mass Index) Calculator, metric + imperial
- `age-calculator` — Age Calculator (years / months / days / total weeks / total days)

### Maths
- `prime-factorization` — Prime Factorization (factors, all divisors, divisor count + sum)
- `roman-numeral` — Roman Numeral Converter (number ↔ Roman, 1–3999)

### Science
- `ph-acid-base` — pH / acid-base calculator (pH ↔ pOH ↔ [H⁺] ↔ [OH⁻]; strong/weak acid/base pH from concentration and Ka/Kb)

## Backlog

_(empty — ask the user what to build next)_
