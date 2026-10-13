"""Serves the built site to the browser tests.

The site is static files, so the standard library's file server is the whole fixture. These
tests need no network: the pages load nothing from outside themselves.
"""

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

DIST = Path(__file__).resolve().parents[2] / "site" / "dist"


@pytest.fixture(scope="session")
def site_url():
    # Fail, never skip: a skipped browser test in CI would read as a pass.
    assert (
        DIST / "index.html"
    ).exists(), "Build the site first: npm --prefix site run build"

    handler = partial(SimpleHTTPRequestHandler, directory=str(DIST))
    # port 0 = let the OS pick a free port
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join()
