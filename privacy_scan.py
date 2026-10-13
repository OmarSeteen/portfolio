"""Refuse a commit that carries a phone number or a listed private term.

This repository is public and git keeps every pushed version for good, so the check has to
run before a commit exists: the pre-commit hook calls it on the staged files. CI runs it
again over every tracked file as a backstop, after the fact.

    python privacy_scan.py            every tracked file, as it is on disk
    python privacy_scan.py --staged   only what the next commit would contain

Findings print as `path:line: reason` and never echo the matched text, because CI logs on a
public repository are public too.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Egyptian mobile numbers. Locally 01x xxxx xxxx; internationally the same without the 0,
# after +20 or 0020. Operators own the prefixes 10, 11, 12 and 15. Up to two separator
# characters may sit between digits, which covers "+20 106 ..." and "(+20) 106 ...".
# A bare 20 prefix is matched only with no separators (the form wa.me links use): with
# separators allowed, two dates side by side ("2011-01-01 2011-01-02") would match.
# The lookarounds keep a digit run inside a longer token, such as a lock-file hash, from
# matching.
# ponytail: Egyptian mobiles only, because that is the number at risk. Landlines and other
# countries pass. Upgrade path: the `phonenumbers` library.
_SEP = r"[ \-.()]{0,2}"
EGYPT_MOBILE = re.compile(
    r"(?<![\w+])(?:"
    r"(?:\+20|0020|0)" + _SEP + r"1[0125](?:" + _SEP + r"\d){8}"
    r"|201[0125]\d{8}"
    r")(?!\w)"
)

# Exact values that must never be committed, one per line: a phone number in any spelling,
# a home address. The file is git-ignored and exists only on the laptop, so this half of the
# scan runs in the hook and not in CI.
PRIVATE_TERMS_FILE = ROOT / "data" / "private_terms.txt"

# A term shorter than this would match ordinary text on almost every line.
MIN_TERM_LENGTH = 6

_IGNORED_IN_TERMS = re.compile(r"[\s\-.()+]")

# git answers in well under a second; this only stops a hung process blocking a commit.
GIT_TIMEOUT_SECONDS = 30


def _squash(text: str) -> str:
    """Drop spacing and punctuation so "+20 106 588" and "20106588" compare equal."""
    return _IGNORED_IN_TERMS.sub("", text).casefold()


def load_private_terms(path: Path = PRIVATE_TERMS_FILE) -> list[str]:
    """Read the laptop-only list. A missing file is normal (CI, a fresh clone)."""
    if not path.exists():
        return []
    terms = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        term = _squash(line)
        if len(term) < MIN_TERM_LENGTH:
            print(
                f"privacy scan: ignoring a private term shorter than "
                f"{MIN_TERM_LENGTH} characters",
                file=sys.stderr,
            )
            continue
        terms.append(term)
    return terms


def scan_text(text: str, private_terms: list[str] = ()) -> list[tuple[int, str]]:
    """Return (line number, reason) for each line that must not be committed."""
    findings = []
    for number, line in enumerate(text.splitlines(), start=1):
        if EGYPT_MOBILE.search(line):
            findings.append((number, "phone number"))
        squashed = _squash(line)
        if any(term in squashed for term in private_terms):
            findings.append((number, "private term"))
    return findings


def _git(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        timeout=GIT_TIMEOUT_SECONDS,
    ).stdout


def _names(output: bytes) -> list[str]:
    return [name.decode("utf-8") for name in output.split(b"\0") if name]


def _files(root: Path, staged: bool) -> list[tuple[str, bytes]]:
    """Pair each file name with the bytes to scan.

    Staged mode reads git's copy of the file, not the one on disk: a file can be staged and
    then edited again, and only the staged version is what the commit will hold.
    """
    if staged:
        names = _names(
            _git(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z")
        )
        return [(name, _git(root, "show", f":{name}")) for name in names]
    files = []
    for name in _names(_git(root, "ls-files", "-z")):
        path = root / name
        # Tracked but deleted on disk: nothing to scan until the deletion is committed.
        if path.is_file():
            files.append((name, path.read_bytes()))
    return files


def scan(root: Path = ROOT, staged: bool = False) -> list[str]:
    """Scan the repository at `root` and return one `path:line: reason` per finding."""
    private_terms = load_private_terms(root / "data" / "private_terms.txt")
    findings = []
    for name, data in _files(root, staged):
        # ponytail: binary files (images) are skipped, not parsed. The CV documents that do
        # carry a phone number are git-ignored by extension instead.
        if b"\0" in data:
            continue
        text = data.decode("utf-8", errors="replace")
        for number, reason in scan_text(text, private_terms):
            findings.append(f"{name}:{number}: {reason}")
    return findings


def main(argv: list[str]) -> int:
    findings = scan(staged="--staged" in argv)
    for finding in findings:
        print(finding)
    if findings:
        print(
            f"privacy scan: {len(findings)} finding(s). Remove them before committing.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
