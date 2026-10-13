"""The laptop-only boundary: its one home.

The admin has no login. What keeps it private is that nothing off this laptop can reach it,
so both ways in are checked here: the address the server binds to, and where each request
comes from.
"""

from flask import abort, request

from .config import ADMIN_HOST, LOOPBACK_ADDRESSES


def assert_loopback_bind(host: str) -> None:
    """Refuse to serve on any address another device could reach."""
    if host != ADMIN_HOST:
        raise RuntimeError(
            f"The admin serves on {ADMIN_HOST} only, and was asked to serve on {host}. "
            "It has no login, so any other address would expose it to the network."
        )


def reject_remote_requests() -> None:
    """Turn away a request that did not start on this laptop.

    Second line of defence. `serve` checks the bind address, but the app can be started
    another way (`flask run --host 0.0.0.0`) that never calls it, so each request is checked
    as well.
    """
    if request.remote_addr not in LOOPBACK_ADDRESSES:
        abort(403)
