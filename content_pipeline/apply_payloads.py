"""Apply every audited payload to the blog via update_article.update().

Single writer for blog/*.html and blog/index.json by design - the parallel
writers only ever produced payload JSON, never touched the blog.

Refuses to run if audit_payloads.py would fail anything.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAYLOADS = HERE / "rewrite_payloads"

sys.path.insert(0, str(HERE))
from update_article import update  # noqa: E402

print("=" * 70)
print("AUDIT GATE - payloads must pass before anything is written")
print("=" * 70)
rc = subprocess.call([sys.executable, str(HERE / "audit_payloads.py")],
                     cwd=str(HERE))
if rc != 0:
    print("\n[ABORT] audit failed - refusing to write to the blog")
    raise SystemExit(1)

payloads = sorted(PAYLOADS.glob("*.json"))
print(f"\n{'=' * 70}\nAPPLYING {len(payloads)} PAYLOADS\n{'=' * 70}")

fails = []
for p in payloads:
    print()
    rc = update(p.stem, __import__("json").loads(
        p.read_text(encoding="utf-8-sig")))
    if rc != 0:
        fails.append(p.stem)

print()
print("=" * 70)
if fails:
    print(f"FAILED: {fails}")
    raise SystemExit(1)
print(f"all {len(payloads)} payloads applied to blog/*.html and index.json")