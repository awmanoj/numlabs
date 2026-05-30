"""Salary take-home (net pay) calculator, by country.

Given an annual GROSS salary, estimate the annual NET (take-home) pay for a
single person with no dependants, using each country's headline income-tax
bands plus the main employee social / payroll contributions.

This is deliberately a ROUGH estimate. Real payslips depend on things this tool
ignores: marital / filing status, dependants, pensions and salary sacrifice,
student-loan repayments, regional / state / provincial taxes, low-income
reliefs and shading thresholds, surcharges, and the exact tax year. Every
country carries `notes` spelling out the biggest simplifications. Not tax
advice — check official figures or a professional before relying on a number.

Tax-year basis: US 2024 (single), UK 2024/25 (England/Wales/NI),
Canada 2024 (federal only), Australia 2024/25 (resident),
India FY 2024/25 new regime, Ireland 2024 (single).
"""

INF = float("inf")


def _marginal(income, bands):
    """Sum marginal tax across ascending bands.

    `bands` is a list of (lower_bound, rate); each rate applies to the slice of
    income from its lower_bound up to the next band's lower_bound (or infinity
    for the last band). Income at or below 0 pays nothing.
    """
    if income <= 0:
        return 0.0
    tax = 0.0
    n = len(bands)
    for i in range(n):
        lo, rate = bands[i]
        hi = bands[i + 1][0] if i + 1 < n else INF
        if income > lo:
            tax += (min(income, hi) - lo) * rate
        else:
            break
    return tax


# --- Per-country models -------------------------------------------------
# Each returns a dict: {"lines": [(label, amount), ...], "taxable": x,
# "notes": [str, ...]}. The first line is always the headline income tax.


def _us(gross):
    std = 14600.0  # standard deduction, single, 2024
    taxable = max(0.0, gross - std)
    bands = [
        (0, 0.10), (11600, 0.12), (47150, 0.22), (100525, 0.24),
        (191950, 0.32), (243725, 0.35), (609350, 0.37),
    ]
    fed = _marginal(taxable, bands)
    ss = min(gross, 168600.0) * 0.062  # Social Security, wage base $168,600
    medicare = gross * 0.0145 + max(0.0, gross - 200000.0) * 0.009
    return {
        "lines": [
            ("Federal income tax", fed),
            ("Social Security (6.2%)", ss),
            ("Medicare (1.45% +0.9%)", medicare),
        ],
        "taxable": taxable,
        "notes": [
            "Single filer, 2024 federal brackets; standard deduction "
            "$14,600 applied.",
            "FEDERAL ONLY — state and local income tax are not included and "
            "vary a lot (0% in some states, ~13% in others).",
            "No credits beyond the standard deduction; 401(k) and other "
            "pre-tax deductions ignored.",
        ],
    }


def _uk(gross):
    pa = 12570.0  # personal allowance, tapered above £100k
    if gross > 100000:
        pa = max(0.0, 12570.0 - (gross - 100000.0) / 2.0)
    basic_limit = 50270.0
    higher_limit = 125140.0
    tax = 0.0
    tax += max(0.0, min(gross, basic_limit) - pa) * 0.20
    tax += max(0.0, min(gross, higher_limit) - basic_limit) * 0.40
    tax += max(0.0, gross - higher_limit) * 0.45
    # Employee National Insurance (Class 1), 2024/25: 8% then 2%.
    ni = max(0.0, min(gross, 50270.0) - 12570.0) * 0.08
    ni += max(0.0, gross - 50270.0) * 0.02
    return {
        "lines": [
            ("Income tax", tax),
            ("National Insurance", ni),
        ],
        "taxable": max(0.0, gross - pa),
        "notes": [
            "England / Wales / Northern Ireland rates, 2024/25 — Scotland "
            "has different bands.",
            "Personal allowance £12,570, tapered away between £100k and "
            "£125,140.",
            "Employee NI at 8% / 2%. Pension auto-enrolment, student-loan "
            "repayments and salary sacrifice are not included.",
        ],
    }


def _ca(gross):
    bpa = 15705.0  # basic personal amount, 2024 (top-earner taper ignored)
    bands = [
        (0, 0.15), (55867, 0.205), (111733, 0.26),
        (173205, 0.29), (246752, 0.33),
    ]
    gross_tax = _marginal(gross, bands)
    fed = max(0.0, gross_tax - bpa * 0.15)
    return {
        "lines": [
            ("Federal income tax", fed),
        ],
        "taxable": gross,
        "notes": [
            "FEDERAL income tax only, 2024 — provincial / territorial tax is "
            "NOT included and is substantial (roughly 4–25% more).",
            "CPP and EI contributions are not included.",
            "Basic personal amount C$15,705 applied as a 15% credit; no "
            "other credits.",
        ],
    }


def _au(gross):
    bands = [
        (0, 0.0), (18200, 0.16), (45000, 0.30),
        (135000, 0.37), (190000, 0.45),
    ]
    tax = _marginal(gross, bands)
    levy = 0.02 * gross if gross > 26000 else 0.0  # Medicare levy
    return {
        "lines": [
            ("Income tax", tax),
            ("Medicare levy (2%)", levy),
        ],
        "taxable": gross,
        "notes": [
            "Resident rates, 2024/25; the $18,200 tax-free threshold is built "
            "in.",
            "Medicare levy 2% (low-income shading near the threshold "
            "ignored). Medicare levy surcharge and HELP/HECS not included.",
            "Superannuation is paid on top by the employer, so it is not "
            "deducted here.",
        ],
    }


def _in(gross):
    std = 75000.0  # standard deduction, new regime FY 2024/25
    taxable = max(0.0, gross - std)
    bands = [
        (0, 0.0), (300000, 0.05), (700000, 0.10), (1000000, 0.15),
        (1200000, 0.20), (1500000, 0.30),
    ]
    tax = _marginal(taxable, bands)
    if taxable <= 700000:
        tax = 0.0  # Section 87A rebate (full rebate up to ₹7,00,000)
    cess = tax * 0.04  # health & education cess
    return {
        "lines": [
            ("Income tax", tax),
            ("Health & education cess (4%)", cess),
        ],
        "taxable": taxable,
        "notes": [
            "New tax regime, FY 2024/25 (AY 2025/26); standard deduction "
            "₹75,000 applied.",
            "Section 87A rebate makes tax nil up to ₹7,00,000 taxable "
            "income; marginal relief just above that is not modelled.",
            "Employee EPF / PF contributions and professional tax are not "
            "included.",
        ],
    }


def _ie(gross):
    # Income tax: 20% standard-rate band to €42,000, 40% above (single).
    gross_tax = _marginal(gross, [(0, 0.20), (42000, 0.40)])
    credits = 1875.0 + 1875.0  # personal + employee (PAYE) tax credits, 2024
    income_tax = max(0.0, gross_tax - credits)
    if gross <= 13000:
        usc = 0.0  # USC exemption
    else:
        usc = _marginal(gross, [(0, 0.005), (12012, 0.02),
                                (25760, 0.04), (70044, 0.08)])
    prsi = gross * 0.04  # Class A employee PRSI
    return {
        "lines": [
            ("Income tax (PAYE)", income_tax),
            ("USC", usc),
            ("PRSI (4%)", prsi),
        ],
        "taxable": gross,
        "notes": [
            "Single person, 2024; standard-rate band €42,000.",
            "Tax credits €3,750 (personal + PAYE) applied; USC is exempt "
            "below €13,000.",
            "PRSI 4% (rose to 4.1% in Oct 2024); pension and other reliefs "
            "not included.",
        ],
    }


# code -> (display name, currency symbol, ISO code, model fn, default gross)
_DISPATCH = {
    "us": ("United States", "$", "USD", _us, 75000),
    "uk": ("United Kingdom", "£", "GBP", _uk, 50000),
    "ca": ("Canada", "C$", "CAD", _ca, 80000),
    "au": ("Australia", "A$", "AUD", _au, 90000),
    "in": ("India", "₹", "INR", _in, 1200000),
    "ie": ("Ireland", "€", "EUR", _ie, 50000),
}


def countries():
    """List of {code, name, currency, currency_code, default_gross} for the UI."""
    return [
        {
            "code": code,
            "name": name,
            "currency": sym,
            "currency_code": iso,
            "default_gross": default,
        }
        for code, (name, sym, iso, _fn, default) in _DISPATCH.items()
    ]


def take_home(country, gross):
    country = str(country).lower()
    if country not in _DISPATCH:
        raise ValueError(f"Unknown country: {country}")
    gross = float(gross)
    if gross < 0:
        raise ValueError("Salary can't be negative")

    name, sym, iso, fn, _default = _DISPATCH[country]
    model = fn(gross)
    lines = model["lines"]
    total = sum(amount for _label, amount in lines)
    net = gross - total

    return {
        "country": country,
        "country_name": name,
        "currency": sym,
        "currency_code": iso,
        "gross": gross,
        "gross_monthly": gross / 12.0,
        "taxable": model["taxable"],
        "lines": [{"label": label, "amount": amount} for label, amount in lines],
        "income_tax": lines[0][1] if lines else 0.0,
        "total_deductions": total,
        "net_annual": net,
        "net_monthly": net / 12.0,
        "effective_rate": (total / gross * 100.0) if gross > 0 else 0.0,
        "notes": model["notes"],
    }


if __name__ == "__main__":
    import math

    # United States: $75,000 single.
    r = take_home("us", 75000)
    # taxable 60,400 -> fed 8,341; SS 4,650; Medicare 1,087.50
    assert math.isclose(r["taxable"], 60400.0)
    assert math.isclose(r["income_tax"], 8341.0), r["income_tax"]
    assert math.isclose(r["total_deductions"], 8341.0 + 4650.0 + 1087.5)
    assert math.isclose(r["net_annual"], 75000 - (8341.0 + 4650.0 + 1087.5))
    print(f"US  $75,000 -> net ${r['net_annual']:,.0f} "
          f"({r['effective_rate']:.1f}% deducted)")

    # United Kingdom: £50,000.
    r = take_home("uk", 50000)
    # tax: 20% on (50,000-12,570)=37,430 -> 7,486; NI 8% on 37,430 -> 2,994.40
    assert math.isclose(r["income_tax"], 7486.0), r["income_tax"]
    assert math.isclose(r["lines"][1]["amount"], 37430.0 * 0.08)
    print(f"UK  £50,000 -> net £{r['net_annual']:,.0f}")

    # UK personal-allowance taper kicks in above £100k.
    r = take_home("uk", 125140)
    assert math.isclose(r["taxable"], 125140.0)  # allowance fully tapered away
    print(f"UK  £125,140 -> allowance gone, taxable £{r['taxable']:,.0f}")

    # Canada: federal only, C$80,000.
    r = take_home("ca", 80000)
    # 15% on 55,867 + 20.5% on 24,133 = 13,327.265; minus 15% of 15,705
    expected = 55867 * 0.15 + (80000 - 55867) * 0.205 - 15705 * 0.15
    assert math.isclose(r["income_tax"], expected), r["income_tax"]
    print(f"CA  C$80,000 -> net (federal only) C${r['net_annual']:,.0f}")

    # Australia: A$90,000.
    r = take_home("au", 90000)
    expected = (45000 - 18200) * 0.16 + (90000 - 45000) * 0.30
    assert math.isclose(r["income_tax"], expected), r["income_tax"]
    assert math.isclose(r["lines"][1]["amount"], 90000 * 0.02)
    print(f"AU  A$90,000 -> net A${r['net_annual']:,.0f}")

    # India: ₹12,00,000 new regime.
    r = take_home("in", 1200000)
    # taxable 11,25,000 -> 5% of 4L + 10% of 3L + 15% of 1.25L = 68,750; cess 4%
    assert math.isclose(r["income_tax"], 68750.0), r["income_tax"]
    assert math.isclose(r["lines"][1]["amount"], 68750.0 * 0.04)
    print(f"IN  Rs 12,00,000 -> net Rs {r['net_annual']:,.0f}")

    # India 87A rebate: ₹7,50,000 gross -> taxable 6,75,000 <= 7L -> tax 0.
    r = take_home("in", 750000)
    assert math.isclose(r["income_tax"], 0.0), r["income_tax"]
    assert math.isclose(r["total_deductions"], 0.0)
    print("IN  87A rebate: Rs 7,50,000 -> Rs 0 income tax")

    # Ireland: €50,000.
    r = take_home("ie", 50000)
    inc = 42000 * 0.20 + 8000 * 0.40 - 3750
    usc = (12012 * 0.005 + (25760 - 12012) * 0.02 + (50000 - 25760) * 0.04)
    assert math.isclose(r["income_tax"], inc), r["income_tax"]
    assert math.isclose(r["lines"][1]["amount"], usc), r["lines"][1]["amount"]
    assert math.isclose(r["lines"][2]["amount"], 50000 * 0.04)
    print(f"IE  EUR 50,000 -> net EUR {r['net_annual']:,.0f}")

    # Zero salary everywhere -> zero deductions, zero net.
    for code in _DISPATCH:
        r = take_home(code, 0)
        assert math.isclose(r["total_deductions"], 0.0)
        assert math.isclose(r["net_annual"], 0.0)
    print("zero-salary edge case OK for all countries")

    # Error cases.
    for bad in [("us", -1), ("zz", 50000)]:
        try:
            take_home(*bad)
        except ValueError as e:
            print(f"take_home{bad} -> {e}")

    # countries() metadata sane.
    cs = countries()
    assert len(cs) == len(_DISPATCH)
    assert all(c["code"] and c["currency"] for c in cs)

    print("all checks passed")
