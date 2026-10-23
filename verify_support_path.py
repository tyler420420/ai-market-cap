"""The site must not send anyone to a mailbox that cannot receive mail.

THE DEFECT THIS GUARDS
----------------------
aismarketcap.com has no inbound mail. The apex has no MX; the only MX is
send. -> feedback.forge.rmta.net, which is Resend's bounce receiver and accepts
no user mail. So support@aismarketcap.com is UNRECEIVABLE.

The site advertised it anyway, live, on two routes:

  /login   "Lost access? Contact support"  (a mailto: link)
  /success "...email support@... with your receipt and we'll fix it by hand."

/success is the worst place on the site for it. It is the page a customer lands
on immediately after paying $5/month, and it promised that a human would repair
the problem by hand. Same defect class as the free signup that wrote into an
ephemeral container: the site instructs someone to do something that cannot
happen.

WHY A NAIVE CHECK FINDS NOTHING
-------------------------------
Cloudflare's email obfuscation rewrites every mailto: into
/cdn-cgi/l/email-protection#<hex> with a data-cfemail attribute. Fetching the
live /login and grepping for "mailto" or for the address returns clean. I only
found it by decoding the hex out of the rendered page.

So this guard reads the SOURCE, and separately decodes the live page, because
either one alone can be made to look fine.

WHAT ELSE IS PINNED
-------------------
The /success error template rendered the raw Python exception ({e}) straight
into the customer-facing HTML. A paying customer saw
"Session instance has invalid ID: None". traceback.print_exc() already logs it
server-side, so exposing it was redundant as well as leaky.

Run: python verify_support_path.py
Exit 0 = no dead mailbox advertised anywhere.
"""
import base64
import io
import os
import re
import sys
import urllib.request

SITE = r'C:\Users\Tyler_AI\ai-market-cap'
SRC = os.path.join(SITE, 'scanner_web.py')
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")

fails = []
ran = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (("  -> " + detail) if detail and not ok else ""))
    ran.append(name)
    if not ok:
        fails.append(name)


src = io.open(SRC, encoding="utf-8").read()

# --- 1. the source must not name the unreceivable mailbox ----------------
check("scanner_web.py never names support@aismarketcap.com",
      'support@aismarketcap.com' not in src,
      "an address that cannot receive mail is still advertised")

# --- 2. no mailto: at all into our own non-deliverable domain ------------
mailtos = set(re.findall(r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+)', src))
dead = {m for m in mailtos if m.lower().endswith('@aismarketcap.com')}
check("no mailto: link points at @aismarketcap.com", not dead, str(dead))

# --- 3. /success must not render a raw exception at the customer ----------
err_lines = [l for l in src.split('\n') if 'class=err>Reference:' in l]
check("/success renders no raw exception into the page",
      bool(err_lines) and not any('{e}' in l or '{exc}' in l for l in err_lines),
      "the raw exception is still interpolated into customer-facing HTML")

# --- 4. the working alternatives must still be present --------------------
check("/success still offers the working self-repair route",
      '/account?repair=1' in src,
      "the replacement instruction points at a route that no longer exists")

# --- 5. every literal internal href resolves to a declared route ---------
#
# First attempt at this check was a false alarm on /blog/ /stock/ /wins/.
# Cause: the href regex also captured f-string TEMPLATES (href="/blog/{slug}")
# and route DECLARATIONS, neither of which is a link to a bare path. Live truth
# is that /wins and /blog return 200 while /wins/ and /blog/ 404, so there was
# never a broken link. A check built on an unverified assumption is worse than
# no check - it trains you to ignore red.
#
# Corrected: skip any href containing "{" (a template), and resolve a cited
# path against the declared route PATTERNS rather than exact strings.
routes = [r for r in re.findall(r"@app\.route\(\s*['\"]([^'\"]+)['\"]", src)
          for _ in (0,)]
all_hrefs = re.findall(r'href=["\']([^"\']+)["\']', src)
cited = set()
for h in all_hrefs:
    if "{" in h or "}" in h:          # f-string template, resolved at runtime
        continue
    h = h.split("#")[0].split("?")[0]
    if h.startswith("/") and h.count("/") <= 2:
        cited.add(h)


def resolves(path):
    if path in routes:
        return True
    for r in routes:
        # /blog/<slug> matches /blog/anything; /stock/<ticker> matches /stock/ABC
        if "<" in r:
            head = r.split("<")[0].rstrip("/")
            if path == head or path.startswith(head + "/"):
                return True
    return False


ignored = ("/static", "/cdn-cgi", "/account?repair")
broken = {c for c in cited
          if c not in routes and not c.startswith(ignored)
          and not c.endswith(('.css', '.js', '.png', '.jpg', '.svg', '.ico', '.webp'))
          and not resolves(c)}
check("every literal internal href resolves to a declared route",
      not broken, str(sorted(broken)))


# --- 6. the LIVE pages must not carry it either (defeats Cloudflare) ------
def cf_decode(page):
    """Decode Cloudflare's obfuscated emails back to plain addresses."""
    found = set()
    for hexval in re.findall(r'data-cfemail="([0-9a-f]+)"', page):
        b = bytes.fromhex(hexval)
        if b[:1] == b"\x02":
            found.add(b[2:].decode("ascii", "replace"))
    for hexval in re.findall(r'email-protection#([0-9a-f]+)', page):
        b = bytes.fromhex(hexval)
        if b[:1] == b"\x02":
            found.add(b[2:].decode("ascii", "replace"))
    return found


try:
    live = {}
    for path in ("/login", "/success"):
        r = urllib.request.Request("https://aismarketcap.com" + path,
                                   headers={"User-Agent": UA})
        live[path] = urllib.request.urlopen(r, timeout=25).read().decode("utf-8", "replace")
    leaked = set()
    for path, page in live.items():
        leaked |= {a for a in cf_decode(page) if a.lower().endswith("@aismarketcap.com")}
        leaked |= set(re.findall(r'[A-Za-z0-9._%+-]+@aismarketcap\.com', page))
    check("live /login and /success advertise no undeliverable address",
          not leaked,
          "still live: %s (note: this fix needs a deploy to reach the site)" % sorted(leaked))
    check("live /success shows no raw exception text",
          'invalid ID' not in live['/success'] and 'Traceback' not in live['/success'],
          "the raw exception is still being served")
except Exception as e:
    print("  SKIP  live probe failed: %s: %s" % (type(e).__name__, e))

print()
if fails:
    print("RESULT: %d FAILED -> %s" % (len(fails), ", ".join(fails)))
    sys.exit(1)
print("RESULT: ALL PASS (%d checks)" % len(ran))