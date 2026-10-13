"""Settings for the local admin app, each with the reason it has that value."""

# The admin holds private fields and has no login, so it must answer only on the laptop
# itself. 127.0.0.1 is unreachable from any other device; 0.0.0.0 would answer the whole
# network.
ADMIN_HOST = "127.0.0.1"

# Flask's default 5000 is Firaq's dev server; 5001 lets both run at once.
ADMIN_PORT = 5001

# Host names a browser on this laptop may use to reach the admin. Any other name in the
# Host header means a hostile web page has pointed its own domain at 127.0.0.1 (DNS
# rebinding) to get past the browser's same-origin rule.
TRUSTED_HOSTS = ["127.0.0.1", "localhost"]

# Addresses a request may come from: IPv4 and IPv6 loopback.
LOOPBACK_ADDRESSES = frozenset({"127.0.0.1", "::1"})
