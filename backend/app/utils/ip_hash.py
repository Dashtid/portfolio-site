"""
Keyed IP digest for log lines.

The request log, the unhandled-exception line, the 429 line and the security
events name a client by ``hash_ip(address)``, never by the address: an
HMAC-SHA256 keyed off ``SECRET_KEY``, cut to 16 hex characters. The key is
what defeats the rainbow-table attack that plain ``sha256(ip)`` is vulnerable
to (IPv4 has only ~4.3B possible values, so a precomputed table is feasible
without a key). The digest of one address is the same on every day, so the
requests of one client can be traced through the log; page_views rows do not
carry it (they hold the daily key of app/utils/visitor_key.py).

We reuse ``SECRET_KEY`` rather than introducing a separate ``IP_HASH_SECRET``
to keep secret management lean. The two would leak together in practice
(both live in the same env / Fly secrets store), so an additional secret
adds operational cost without raising the security floor. The
``"ip-hash-v1:"`` domain-separation prefix prevents collisions with any
other future HMAC use of the same key.

Rotating ``SECRET_KEY`` invalidates the mapping — same IP -> different hash —
so log lines from before and after a rotation no longer share a client's
digest. Rotation is already an "everyone gets logged out" event because of
the JWT use.
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

    Deterministic for a given (``SECRET_KEY``, ``ip``) pair, so every log
    line of one address carries the same digest.
    """
    key = (settings.SECRET_KEY or "").encode()
    msg = _DOMAIN_PREFIX + ip.encode()
    return hmac.new(key, msg, hashlib.sha256).hexdigest()[:_HASH_LENGTH]
