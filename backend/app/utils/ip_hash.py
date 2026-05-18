"""
Privacy-preserving IP pseudonymisation for analytics.

Raw visitor IPs are passed through HMAC-SHA256 keyed off ``SECRET_KEY`` before
being stored on the ``PageView`` row. The HMAC construction defeats the
rainbow-table attack that plain ``sha256(ip)`` is vulnerable to (IPv4 has
only ~4.3B possible values, so a precomputed table is feasible without a key).

We reuse ``SECRET_KEY`` rather than introducing a separate ``IP_HASH_SECRET``
to keep secret management lean. The two would leak together in practice
(both live in the same env / Fly secrets store), so an additional secret
adds operational cost without raising the security floor. The
``"ip-hash-v1:"`` domain-separation prefix prevents collisions with any
other future HMAC use of the same key.

Rotating ``SECRET_KEY`` invalidates the mapping — same IP -> different hash.
Existing rows keep their old hashes, so for ~30 days after a rotation a
returning visitor counts as a new visitor in the analytics window. That's an
acceptable, one-time effect; rotation is already an "everyone gets logged
out" event because of the JWT use.
"""

import hashlib
import hmac

from app.config import settings

# Truncated to 16 hex chars (64 bits). Collision probability for the
# realistic visitor population is negligible and matches the previous
# unsalted-sha256 column width so the migration is in-place.
_HASH_LENGTH = 16
_DOMAIN_PREFIX = b"ip-hash-v1:"


def hash_ip(ip: str) -> str:
    """Return a pseudonymous fixed-width hex digest for ``ip``.

    Deterministic for a given (``SECRET_KEY``, ``ip``) pair so repeat
    visits from the same IP collapse to the same hash.
    """
    key = (settings.SECRET_KEY or "").encode()
    msg = _DOMAIN_PREFIX + ip.encode()
    return hmac.new(key, msg, hashlib.sha256).hexdigest()[:_HASH_LENGTH]
