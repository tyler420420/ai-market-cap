#!/usr/bin/env python3
"""Canonical one-click unsubscribe token, shared by both ends.

WHY THIS IS ITS OWN MODULE
Two processes build and verify this token:
  * scanner_web.py  - issues it, inside Railway
  * send_daily_alert.py - embeds it in every outgoing message, on this machine

If those two implementations were duplicated, a change to one would produce
links that the other rejects - silently, on every email, to every recipient,
with no error anywhere except a 400 nobody sees. One module means they cannot
drift.

SELF-CONTAINED ON PURPOSE
The container is ephemeral. A server-side token-to-address map evaporates on
the next deploy and takes every unsubscribe with it, so the address rides
inside the token instead. It is base64url rather than plaintext so it does
not sit readable in proxy access logs.

The key is EMAIL_EXPORT_TOKEN, which is the same single Railway variable the
local machine already uses to pull the list. Two jobs, one secret, nothing to
keep in sync by hand.
"""
import base64
import hashlib
import hmac

UNSUBSCRIBE_PATH = "/api/email-unsubscribe"
SITE_URL = "https://aismarketcap.com"


def _sig(payload, token):
    return hmac.new((token or "").encode(), payload.encode(),
                    hashlib.sha256).hexdigest()[:32]


def unsubscribe_token(email, token):
    """Return the opaque token for an address, or None if no token is set."""
    if not token:
        return None
    payload = base64.urlsafe_b64encode(
        email.strip().lower().encode()).decode().rstrip("=")
    return "%s.%s" % (payload, _sig(payload, token))


def unsubscribe_link(email, token, site_url=SITE_URL):
    """Full one-click URL, or None when EMAIL_EXPORT_TOKEN is not set.

    None is deliberate rather than a broken link: an unconfigured token
    cannot produce a verifiable unsubscribe, and shipping one that 400s would
    be worse than admitting the lane is not set up. The caller is expected to
    surface that instead of quietly mailing without one.
    """
    tok = unsubscribe_token(email, token)
    if not tok:
        return None
    return "%s%s?t=%s" % (site_url.rstrip("/"), UNSUBSCRIBE_PATH, tok)


def parse_unsubscribe(raw, token):
    """Return the address behind a token, or None if it does not verify.

    compare_digest on both the signature and the presence of a key, so a
    caller with no token configured verifies nothing rather than everything.
    """
    if not token or not raw or "." not in raw:
        return None
    payload, _, sig = raw.rpartition(".")
    if not hmac.compare_digest(sig, _sig(payload, token)):
        return None
    try:
        email = base64.urlsafe_b64decode(
            payload + "=" * (-len(payload) % 4)).decode()
    except Exception:
        return None
    return email or None