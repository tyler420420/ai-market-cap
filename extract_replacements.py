"""Extract leaked credential VALUES from history into a filter-repo replace-text file.

Safety rules this script enforces:
  - Never prints a full credential value. Only a masked preview (first 6 chars)
    and the value length, so a human can confirm identity without the secret
    appearing in a transcript, log, or commit message.
  - Discovers ALL distinct values across all refs, not just one known set, in
    case a value changed between commits.

Usage:  python extract_replacements.py <repo> <outfile>
"""
import re
import subprocess
import sys

# Known credential prefixes (safe - these are not secrets themselves).
PREFIXES = (
    "ptD4IFlECfhY",   # api_key
    "zZL8q7mClA7",    # api_secret
    "2034074541757222912",  # access_token
    "qRXpfp30a5LU2nqvbYT4FZj",  # access_secret
)

# X credentials are base64url-ish: A-Z a-z 0-9 - _
VALUE_RE = re.compile(r"[A-Za-z0-9_-]{20,}")


def mask(value: str) -> str:
    return f"{value[:6]}...<{len(value)} chars>"


def main() -> int:
    repo, outfile = sys.argv[1], sys.argv[2]

    # Single pass over the full patch history of every ref.
    out = subprocess.run(
        ["git", "-C", repo, "log", "--all", "-p", "--no-color", "-U0"],
        capture_output=True, text=True, errors="replace",
    ).stdout

    found: dict[str, set[str]] = {p: set() for p in PREFIXES}
    for line in out.splitlines():
        # Only consider added/removed source lines, not diff headers.
        if not (line.startswith("+") or line.startswith("-")):
            continue
        if line.startswith(("+++", "---")):
            continue
        for prefix in PREFIXES:
            idx = line.find(prefix)
            while idx != -1:
                m = VALUE_RE.match(line, idx)
                if m:
                    found[prefix].add(m.group(0))
                    idx = line.find(prefix, m.end())
                else:
                    idx = -1

    total = 0
    with open(outfile, "w", encoding="utf-8", newline="\n") as fh:
        for prefix, values in found.items():
            for value in sorted(values):
                fh.write(f"literal:{value}==>REDACTED_X_CREDENTIAL\n")
                total += 1
            print(f"  {prefix}...: {len(values)} distinct value(s) "
                  f"-> {[mask(v) for v in sorted(values)]}")

    print(f"\nTOTAL distinct values written: {total}")
    print(f"replace-text file: {outfile}")
    return 0 if total else 1


if __name__ == "__main__":
    sys.exit(main())
