"""Move gate-rejected articles back into the main queue for a re-check.

Use after manually fixing the issues the gate flagged (e.g. adding concrete
numbers). The gate keeps rejected files instead of deleting them, so nothing
is ever lost.
"""
import shutil
import sys
from pathlib import Path

QUEUE = Path(__file__).resolve().parent / "article_queue"
REJECTED = QUEUE / "rejected"


def main(names):
    if not REJECTED.exists():
        print("  (no rejected dir)")
        return 0
    moved = 0
    targets = list(REJECTED.glob("*.json")) if not names else [
        REJECTED / n for n in names]
    for src in targets:
        if src.exists():
            dest = QUEUE / src.name
            shutil.move(str(src), str(dest))
            print(f"  [MOVED] {src.name} -> queue")
            moved += 1
    return moved


if __name__ == "__main__":
    n = main(sys.argv[1:])
    print(f"\n[OK] {n} article(s) returned to queue for re-gating.")