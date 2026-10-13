"""The scan is the last check before a private value becomes permanent public history.

Every phone number below is assembled at run time. A literal one in this file would make the
scan reject the file that tests it.
"""

import subprocess

import pytest

from privacy_scan import load_private_terms, scan, scan_text

LOCAL = "010" + "1234" + "5678"
NATIONAL = LOCAL[1:]


@pytest.mark.parametrize(
    "text",
    [
        LOCAL,
        f"call {LOCAL[:3]} {LOCAL[3:7]} {LOCAL[7:]} today",
        f"+20{NATIONAL}",
        f"+20 {NATIONAL[:3]} {NATIONAL[3:6]} {NATIONAL[6:]}",
        f"(+20) {NATIONAL[:3]}-{NATIONAL[3:6]}-{NATIONAL[6:]}",
        f"0020{NATIONAL}",
        f"https://wa.me/20{NATIONAL}",
        f'<a href="tel:{LOCAL}">',
    ],
)
def test_phone_number_is_found_in_every_spelling(text):
    assert scan_text(text) == [(1, "phone number")]


@pytest.mark.parametrize(
    "text",
    [
        "Dec 2023 to Aug 2025",
        '"start": "2025-12", "end": "2026-10"',
        "2011-01-01 2011-01-02",
        "90% on-time across 30+ client accounts, 120 looms",
        "sha256:" + "a" + LOCAL + "f" * 52,
        "180476909+OmarSeteen@users.noreply.github.com",
    ],
)
def test_ordinary_text_passes(text):
    assert scan_text(text) == []


def test_finding_reports_the_line_and_never_the_number():
    findings = scan_text(f"first line\nphone: {LOCAL}\n")
    assert findings == [(2, "phone number")]
    assert LOCAL not in str(findings)


def test_private_term_is_found_however_it_is_spaced(tmp_path):
    terms_file = tmp_path / "private_terms.txt"
    terms_file.write_text("# my street\n12 Example Street\n\nab\n", encoding="utf-8")
    terms = load_private_terms(terms_file)

    assert terms == ["12examplestreet"]  # the comment, the blank and "ab" are dropped
    assert scan_text("lives at 12  example-street", terms) == [(1, "private term")]
    assert scan_text("lives on another street", terms) == []


def test_missing_private_terms_file_is_not_an_error(tmp_path):
    assert load_private_terms(tmp_path / "absent.txt") == []


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    """A throwaway git repository. No test here touches the real one or the network."""
    git(tmp_path, "init")
    return tmp_path


def test_staged_scan_reads_what_the_commit_would_hold(repo):
    """The hook path: a number staged and then edited out on disk is still in the commit."""
    cv = repo / "cv.json"
    cv.write_text(f'{{"phone": "{LOCAL}"}}\n', encoding="utf-8")
    git(repo, "add", "cv.json")
    cv.write_text('{"phone": null}\n', encoding="utf-8")

    assert scan(repo, staged=True) == ["cv.json:1: phone number"]


def test_tracked_scan_reads_the_files_on_disk_and_skips_binaries(repo):
    (repo / "clean.txt").write_text("nothing private\n", encoding="utf-8")
    (repo / "leak.txt").write_text(f"ok\n{LOCAL}\n", encoding="utf-8")
    (repo / "photo.bin").write_bytes(b"\0\1" + LOCAL.encode())
    git(repo, "add", ".")

    assert scan(repo) == ["leak.txt:2: phone number"]


def test_private_terms_file_inside_the_repo_is_used(repo):
    (repo / "data").mkdir()
    (repo / "data" / "private_terms.txt").write_text(NATIONAL + "\n", encoding="utf-8")
    # Percent-encoded "+20...": the phone pattern misses it, the private term catches it.
    (repo / "page.html").write_text(f"wa.me/%2B20{NATIONAL}\n", encoding="utf-8")
    git(repo, "add", "page.html")

    assert scan(repo, staged=True) == ["page.html:1: private term"]
