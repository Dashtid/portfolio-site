"""The API's security.txt (RFC 9116) lists only working channels and stays current.

frontend/tests/unit/securityTxt.spec.ts applies the same rules to the site's
copy, frontend/public/.well-known/security.txt; only the two serving checks
here are the API's own. A renewal changes the Expires line in both files, and
.github/workflows/security-txt-expiry.yml checks both live copies every week.
"""

import re
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.main import SECURITY_TXT_CONTENT

CANONICAL = "https://api.dashti.se/.well-known/security.txt"
POLICY = "https://github.com/Dashtid/portfolio-site/blob/main/SECURITY.md"
PVR = "https://github.com/Dashtid/portfolio-site/security/advisories/new"
LINKEDIN = "https://www.linkedin.com/in/david-dashti/"
# RFC 9116 section 2.5.5 recommends an Expires less than a year ahead. No
# calendar year is shorter than 365 days, so under 365 days is always under a
# year. The 30-day margin turns CI red before the file goes stale, not after.
RENEW_MARGIN = timedelta(days=30)
MAX_AHEAD = timedelta(days=365)
# The date-time of RFC 3339 section 5.6, which section 2.5.5 requires, with an
# upper-case T and Z only. RFC 3339 also allows a lower-case t and z, but
# fromisoformat here rejects the z that Date.parse in the frontend accepts.
# re.ASCII keeps \d to 0-9, as it is in JavaScript.
RFC3339 = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})", re.ASCII)
# An offset's hours run 00-23 and its minutes 00-59 (RFC 3339 section 5.6).
OFFSET = re.compile(r"Z|[+-]([01]\d|2[0-3]):[0-5]\d")
# A field is a name, a colon, one space and a non-empty value (the ABNF's
# "fs SP"). The name is RFC 5322's field-name: visible ASCII except the colon.
FIELD = re.compile(r"[!-9;-~]+: \S.*")
# The email and phone shapes of frontend/tests/unit/cvPublicScrub.spec.ts.
EMAIL = re.compile(r"\S+@\S+\.\S+")
PHONE = re.compile(r"\+\d[\d\s-]{7,}")

LINES = re.split(r"\r?\n", SECURITY_TXT_CONTENT)


def _fields(name: str) -> list[str]:
    # Field names are case-insensitive (RFC 9116 section 2); "#" starts a comment.
    values = []
    for line in LINES:
        field, sep, value = line.partition(":")
        if sep and not line.startswith("#") and field.strip().lower() == name.lower():
            values.append(value.strip())
    return values


def test_every_line_is_blank_a_comment_or_a_well_formed_field() -> None:
    malformed = [
        line
        for line in LINES
        if line.strip() and not line.startswith("#") and not FIELD.fullmatch(line)
    ]
    assert malformed == []


def test_every_line_ends_with_lf_or_crlf_the_last_one_included() -> None:
    # RFC 9116 section 2.2. A carriage return is allowed only before a line feed.
    assert SECURITY_TXT_CONTENT.endswith("\n")
    assert re.findall(r"\r(?!\n)", SECURITY_TXT_CONTENT) == []


def test_well_known_path_serves_the_file_as_utf8_text(client: TestClient) -> None:
    response = client.get("/.well-known/security.txt")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert response.text == SECURITY_TXT_CONTENT


def test_legacy_path_redirects_to_the_well_known_one(client: TestClient) -> None:
    # RFC 9116 section 3 allows the redirect. Serving the file at /security.txt
    # would fail section 2.5.2: the only Canonical names the /.well-known/ URI.
    response = client.get("/security.txt", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == "/.well-known/security.txt"


def test_contacts_are_the_working_channels_only() -> None:
    # A dashti.se mailbox bounced for as long as one was listed: the domain
    # has no MX record. The channels are SECURITY.md's preferred one and its
    # LinkedIn alternative, GitHub private vulnerability reporting first.
    assert _fields("Contact") == [PVR, LINKEDIN]


def test_no_mailto_tel_email_or_phone_anywhere_comments_included() -> None:
    assert re.findall(r"mailto:|tel:", SECURITY_TXT_CONTENT, re.IGNORECASE) == []
    assert EMAIL.findall(SECURITY_TXT_CONTENT) == []
    assert PHONE.findall(SECURITY_TXT_CONTENT) == []


def test_canonical_is_its_own_url_and_policy_is_security_md() -> None:
    assert _fields("Canonical") == [CANONICAL]
    assert _fields("Policy") == [POLICY]


def test_preferred_languages_appears_at_most_once() -> None:
    # RFC 9116 section 2.5.8: the field MUST NOT appear more than once.
    assert len(_fields("Preferred-Languages")) <= 1


def test_expires_is_set_once_as_rfc3339_more_than_30_and_under_365_days_ahead() -> None:
    values = _fields("Expires")
    assert len(values) == 1, values
    expires = values[0]
    shape = RFC3339.fullmatch(expires)
    assert shape, f"Expires {expires} is not an RFC 3339 date-time (upper-case T and Z)"
    # The pattern alone admits 2027-02-30, T24:00:00 and offsets such as +24:00
    # and +01:60, none of which RFC 3339 allows (sections 5.6 and 5.7: hours
    # 00-23, minutes 00-59, days up to the month's last). fromisoformat raises
    # on 2027-02-30 and +24:00 but reads T24:00:00 as the next midnight and
    # +01:60 as +02:00, so the offset must be in range and the date and time
    # must read back as written. It also refuses the year 0000 and a leap
    # second's :60, which RFC 3339 allows; neither is a plausible Expires.
    try:
        parsed: datetime | None = datetime.fromisoformat(expires)
    except ValueError:
        parsed = None
    assert (
        parsed is not None
        and OFFSET.fullmatch(shape[2]) is not None
        and parsed.isoformat()[:19] == expires[:19]
    ), f"Expires {expires} is not an RFC 3339 date-time: no such date or time"
    ahead = parsed - datetime.now(UTC)
    assert ahead > RENEW_MARGIN, (
        f"Expires {expires} leaves 30 days or less: renew it in backend/app/main.py "
        "(SECURITY_TXT_CONTENT) and in frontend/public/.well-known/security.txt"
    )
    assert ahead < MAX_AHEAD, (
        f"Expires {expires} is 365 days or more ahead; RFC 9116 section 2.5.5 "
        "recommends less than a year"
    )
