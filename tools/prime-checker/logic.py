"""Prime checker — pure-Python logic.

Answers the everyday prime questions about a single integer n:
  - is it prime? if not, the smallest factor that proves it isn't
  - the next prime after it, and the previous prime before it (the prime gap)
  - is it part of a twin-prime pair (p, p+2)?
  - how many primes are <= n  (the prime-counting function pi(n))
  - which prime it is, when it is prime (its index: 2 is the 1st, 3 the 2nd, ...)

Trial division with a 6k+/-1 wheel. Capped at n <= 10**12 so the browser stays
snappy — sqrt(10**12) is 10**6 iterations per primality test, and neighbour
searches only probe a handful of candidates because prime gaps stay small.
Runs standalone: `python3 logic.py`.
"""

MAX_N = 10 ** 12


def is_prime(n):
    """True if n is a prime. Deterministic trial division on a 6k+/-1 wheel."""
    if n < 2:
        return False
    if n < 4:
        return True  # 2 and 3
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def smallest_factor(n):
    """Smallest prime factor of n (n itself if prime). None for n < 2."""
    if n < 2:
        return None
    if n % 2 == 0:
        return 2
    if n % 3 == 0:
        return 3
    i = 5
    while i * i <= n:
        if n % i == 0:
            return i
        if n % (i + 2) == 0:
            return i + 2
        i += 6
    return n


def next_prime(n):
    """Smallest prime strictly greater than n."""
    candidate = n + 1
    if candidate < 2:
        return 2
    while not is_prime(candidate):
        candidate += 1
    return candidate


def prev_prime(n):
    """Largest prime strictly less than n, or None if none exists (n <= 2)."""
    candidate = n - 1
    while candidate >= 2:
        if is_prime(candidate):
            return candidate
        candidate -= 1
    return None


def prime_count(n):
    """pi(n): how many primes are <= n, via a Sieve of Eratosthenes.

    Only used for modest n (the caller guards with a limit) since it allocates
    an n-sized array.
    """
    if n < 2:
        return 0
    sieve = bytearray([1]) * (n + 1)
    sieve[0] = sieve[1] = 0
    i = 2
    while i * i <= n:
        if sieve[i]:
            sieve[i * i::i] = bytearray(len(sieve[i * i::i]))
        i += 1
    return sum(sieve)


def check(n):
    """Full report for n: primality, neighbours, gap, twin status, and index.

    prime_index (which prime n is) and primes_below (pi(n-1)) are only computed
    when n is small enough to sieve quickly; otherwise they come back as None so
    the tool degrades gracefully on huge inputs instead of freezing.
    """
    if not isinstance(n, int):
        n = int(n)
    if n < 0:
        raise ValueError("Enter a whole number 0 or greater")
    if n > MAX_N:
        raise ValueError(f"n must be <= {MAX_N:,}")

    prime = is_prime(n)
    nxt = next_prime(n)
    prv = prev_prime(n)

    # Twin prime: a prime p where p-2 or p+2 is also prime.
    twin_with = None
    if prime:
        if is_prime(n - 2):
            twin_with = n - 2
        elif is_prime(n + 2):
            twin_with = n + 2

    # Cheap counting only when a sieve is affordable.
    SIEVE_LIMIT = 10 ** 7
    if n <= SIEVE_LIMIT:
        primes_below = prime_count(n - 1) if n >= 1 else 0
        prime_index = prime_count(n) if prime else None
    else:
        primes_below = None
        prime_index = None

    return {
        "n": n,
        "is_prime": prime,
        "smallest_factor": smallest_factor(n) if not prime and n >= 2 else None,
        "next_prime": nxt,
        "prev_prime": prv,
        "gap_to_next": nxt - n,
        "gap_from_prev": (n - prv) if prv is not None else None,
        "twin_with": twin_with,
        "prime_index": prime_index,
        "primes_below": primes_below,
        "counts_capped": n > SIEVE_LIMIT,
    }


if __name__ == "__main__":
    assert is_prime(2) and is_prime(3) and is_prime(97)
    assert not is_prime(1) and not is_prime(0) and not is_prime(91)  # 91 = 7*13
    assert smallest_factor(91) == 7
    assert next_prime(89) == 97 and prev_prime(97) == 89
    assert prime_count(10) == 4  # 2,3,5,7
    assert prime_count(100) == 25

    r = check(97)
    assert r["is_prime"] and r["prime_index"] == 25
    assert r["twin_with"] is None  # 95 and 99 are composite, so 97 isn't a twin
    assert check(17)["twin_with"] == 19  # (17, 19) is a twin pair
    assert check(20)["is_prime"] is False and check(20)["smallest_factor"] == 2

    for n in [1, 2, 17, 20, 91, 97, 561, 7919]:
        r = check(n)
        tag = "PRIME" if r["is_prime"] else f"composite (smallest factor {r['smallest_factor']})"
        twin = f", twin with {r['twin_with']}" if r["twin_with"] else ""
        idx = f", the {r['prime_index']}th prime" if r["prime_index"] else ""
        print(f"{n}: {tag}{idx}{twin}")
        print(f"   prev {r['prev_prime']} | next {r['next_prime']} "
              f"(gap to next {r['gap_to_next']}) | primes below: {r['primes_below']}")
