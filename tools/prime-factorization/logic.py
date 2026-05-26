"""Prime factorisation — pure-Python logic.

Given an integer n >= 2, returns its unique prime factorisation:
    n = p1^a1 * p2^a2 * ... * pk^ak

Trial division with a 2,3 wheel (skip multiples of 2 and 3 after handling
them). Capped at n <= 10**13 so the browser stays responsive — sqrt(10**13)
is ~3.2M iterations, which Pyodide handles in well under a second.
"""

MAX_N = 10 ** 13


def factorize(n):
    """Return prime factorisation, divisors, and related properties of n."""
    if not isinstance(n, int):
        n = int(n)
    if n < 2:
        raise ValueError("n must be an integer >= 2")
    if n > MAX_N:
        raise ValueError(f"n must be <= {MAX_N:,}")

    original = n
    factors = []  # list of [prime, exponent]

    for p in (2, 3):
        if n % p == 0:
            e = 0
            while n % p == 0:
                n //= p
                e += 1
            factors.append([p, e])

    # 6k +/- 1 wheel: candidates 5, 7, 11, 13, 17, 19, ...
    p = 5
    while p * p <= n:
        for d in (p, p + 2):
            if n % d == 0:
                e = 0
                while n % d == 0:
                    n //= d
                    e += 1
                factors.append([d, e])
        p += 6

    if n > 1:
        factors.append([n, 1])

    # Generate the full divisor list from the prime power decomposition.
    divisors = [1]
    for prime, exp in factors:
        extension = []
        power = 1
        for _ in range(exp):
            power *= prime
            extension.extend(d * power for d in divisors)
        divisors.extend(extension)
    divisors.sort()

    is_prime = len(factors) == 1 and factors[0][1] == 1

    return {
        "n": original,
        "factors": factors,
        "is_prime": is_prime,
        "divisor_count": len(divisors),
        "divisor_sum": sum(divisors),
        "divisors": divisors,
    }


def _pretty(factors):
    parts = []
    for p, e in factors:
        parts.append(f"{p}^{e}" if e > 1 else str(p))
    return " × ".join(parts)


if __name__ == "__main__":
    samples = [2, 7, 12, 360, 1000, 999983, 2 ** 20, 1234567, 10 ** 12 + 39]
    for n in samples:
        r = factorize(n)
        tag = " (prime)" if r["is_prime"] else ""
        print(f"{n} = {_pretty(r['factors'])}{tag}")
        print(f"   divisors: {r['divisor_count']}, sum: {r['divisor_sum']}")

    # error cases
    for bad in (1, 0, -5):
        try:
            factorize(bad)
        except ValueError as e:
            print(f"{bad}: {e}")
