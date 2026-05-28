"""Currency conversion — pure-Python logic.

Conversion math is trivial (amount * rate), but this module wraps it so the
browser side stays thin and the result is consistently formatted regardless
of currency magnitude (JPY vs. BTC-like big-number quotes).

The live exchange rate is fetched in JS from the European Central Bank via
api.frankfurter.dev and handed to this module as a plain float.
"""


def _decimals_for(value):
    """Pick a sensible number of decimals based on the value's magnitude.

    Big numbers (>=100) -> 2 dp. Small numbers (<1) -> up to 6 dp so a
    cross-rate like 0.011234 USD/JPY does not collapse to 0.01.
    """
    a = abs(value)
    if a == 0:
        return 2
    if a >= 100:
        return 2
    if a >= 1:
        return 4
    if a >= 0.01:
        return 6
    return 8


def convert(amount, rate, from_code, to_code):
    """Convert `amount` of `from_code` into `to_code` at `rate`.

    amount:     numeric amount in the source currency
    rate:       units of `to_code` per 1 unit of `from_code`
    from_code:  ISO 4217 source currency code (e.g. "USD")
    to_code:    ISO 4217 target currency code (e.g. "EUR")

    Returns a dict:
        converted        — amount * rate
        rate             — the rate used (units of `to_code` per `from_code`)
        inverse_rate     — 1 / rate (units of `from_code` per `to_code`)
        decimals         — suggested decimal places for `converted`
        rate_decimals    — suggested decimal places for the rate display
        from_code, to_code, amount — echoed back for the caller's convenience
    """
    converted = amount * rate
    inverse = (1.0 / rate) if rate else 0.0
    return {
        "amount": amount,
        "from_code": from_code,
        "to_code": to_code,
        "rate": rate,
        "inverse_rate": inverse,
        "converted": round(converted, _decimals_for(converted)),
        "decimals": _decimals_for(converted),
        "rate_decimals": _decimals_for(rate),
        "inverse_decimals": _decimals_for(inverse),
    }


if __name__ == "__main__":
    # Sanity check: convert 100 USD -> INR at an example rate.
    r = convert(100, 95.69, "USD", "INR")
    print(f"100 USD = {r['converted']:.{r['decimals']}f} INR")
    print(f"  rate:    1 USD = {r['rate']:.{r['rate_decimals']}f} INR")
    print(f"  inverse: 1 INR = {r['inverse_rate']:.{r['inverse_decimals']}f} USD")

    # Small-rate case: 1 JPY -> USD
    r = convert(1, 0.0064, "JPY", "USD")
    print(f"1 JPY = {r['converted']:.{r['decimals']}f} USD")

    # Same-currency case: rate is 1
    r = convert(50, 1.0, "EUR", "EUR")
    print(f"50 EUR = {r['converted']:.{r['decimals']}f} EUR")
