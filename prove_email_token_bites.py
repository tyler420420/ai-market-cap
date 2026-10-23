"""Mutation proof for the token-normalization checks in verify_email_list.py.

Reintroduces the silent-failure class the CTO found - a secret pasted with a
trailing newline - and three half-fixes of it, one at a time, into throwaway
copies, and requires the guard to reject every one.

Nothing here touches the real files. Each mutant is written to a temp dir
together with every module the guard imports, because the guard imports them
from Path(__file__).parent. Without that copy each mutant would "fail" for
the wrong reason (no module), which would prove nothing.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SITE = Path(r"C:\Users\Tyler_AI\ai-market-cap")
GUARD = SITE / "verify_email_list.py"
GIT = r"C:\Program Files\Git\cmd\git.exe"
FILES = ["scanner_web.py", "email_unsubscribe.py", "send_daily_alert.py",
         "pull_email_list.py", "verify_email_list.py", "scanner_data.json"]
PY = sys.executable

src = {name: (SITE / name).read_text(encoding="utf-8") for name in FILES}

assert "_eu.normalize_token(EMAIL_EXPORT_TOKEN)" in src["scanner_web.py"], \
    "control no longer normalizes the stored token - fix the real file first"


def m_compare_unstripped(f):
    """The CTO's defect: the presented header is stripped, the stored token is not.

    The export then compares a clean header against a newline-terminated
    secret, 403s forever, and every other health check still looks healthy.
    """
    out = dict(f)
    out["scanner_web.py"] = f["scanner_web.py"].replace(
        "    stored = _eu.normalize_token(EMAIL_EXPORT_TOKEN)",
        "    stored = EMAIL_EXPORT_TOKEN")
    return out


def m_hmac_unnormalized(f):
    """Half fix: the comparison normalizes, the HMAC key does not.

    The link this machine mints with the clean secret then fails to verify
    on the service, so every recipient's unsubscribe click 400s - and the
    mail still sends, so nothing reports it.

    All three places have to be mutated together: the raw key has to reach
    the HMAC, and both the signer and the verifier have to stop normalizing
    before they hand it over.
    """
    out = dict(f)
    s = f["email_unsubscribe.py"]
    s = s.replace(
        '    return hmac.new(normalize_token(token).encode(), payload.encode(),',
        '    return hmac.new((token or "").encode(), payload.encode(),')
    s = s.replace(
        "    key = normalize_token(token)\n    if not key:",
        "    key = token\n    if not key:")
    s = s.replace(
        "    key = normalize_token(token)\n    if not key or not raw",
        "    key = token\n    if not key or not raw")
    out["email_unsubscribe.py"] = s
    return out


def m_route_truthy(f):
    """Half fix: the route still treats a whitespace-only token as configured.

    It answers 400 ("bad token") where it should answer 503 ("not
    configured"), and every health check reads 400 as "the route works".
    """
    out = dict(f)
    out["scanner_web.py"] = f["scanner_web.py"].replace(
        "    if not _eu.normalize_token(EMAIL_EXPORT_TOKEN):",
        "    if not EMAIL_EXPORT_TOKEN:")
    return out


def m_normalize_everything(f):
    """Over-corrected: normalization deletes every non-word character.

    A token that differs only by a stray quote now matches the real secret,
    which is a weaker check than the one it replaced.
    """
    out = dict(f)
    out["email_unsubscribe.py"] = f["email_unsubscribe.py"].replace(
        '    tok = (value or "").strip()',
        '    tok = "".join(ch for ch in (value or "") if ch.isalnum() or ch in "_-")')
    return out


MUTANTS = [
    ("stored token compared unstripped (the defect)", m_compare_unstripped),
    ("the HMAC key is not normalized", m_hmac_unnormalized),
    ("a whitespace-only token reads as configured", m_route_truthy),
    ("normalization deletes too much", m_normalize_everything),
]


def run(files, td):
    for name, text in files.items():
        (td / name).write_text(text, encoding="utf-8")
    # The child's stdout is decoded as UTF-8, so the child has to WRITE it as
    # UTF-8. Without this the Windows console codepage emits cp1252 bytes
    # and the parent dies in the reader thread instead of reporting a mutant.
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    p = subprocess.run([PY, str(td / "verify_email_list.py")],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(td), env=env)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


caught = 0
with tempfile.TemporaryDirectory() as tmpdir:
    td = Path(tmpdir)
    # The guard checks that email_list.json and alert.env are gitignored,
    # and it does that with `git -C <its own dir>`. So the sandbox has to be
    # a repo with the same ignore rules, or every mutant "fails" for a
    # reason that has nothing to do with the mutation.
    shutil.copy2(SITE / ".gitignore", td / ".gitignore")
    subprocess.run([GIT, "init", "-q"], cwd=str(td), capture_output=True)
    for extra in ("scanner_data.json",):
        if (SITE / extra).exists():
            shutil.copy2(SITE / extra, td / extra)

    rc, out = run(src, td)
    print("CONTROL rc=%d %s" % (rc, "PASS" if rc == 0 else "FAIL"))
    if rc != 0:
        print(out)
        print("RESULT: control does not pass - the guard proves nothing")
        sys.exit(1)
    print()

    for name, fn in MUTANTS:
        mut = fn(src)
        changed = [k for k in mut if mut[k] != src[k]]
        assert changed, "mutant %r changed nothing - it tests nothing" % name
        rc, out = run(mut, td)
        ok = rc != 0
        caught += ok
        first = next((ln.strip() for ln in out.splitlines()
                      if ln.strip().startswith("FAIL")), "(guard passed)")
        print("  %s  %-46s %s" % ("CAUGHT" if ok else "MISSED", name, first[:66]))

print()
print("RESULT: %d/%d caught" % (caught, len(MUTANTS)))
sys.exit(0 if caught == len(MUTANTS) else 1)
