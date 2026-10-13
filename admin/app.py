"""App factory and launcher for the local admin."""

import secrets

from flask import Flask, render_template
from flask.helpers import get_debug_flag
from flask_wtf.csrf import CSRFProtect

from . import config
from .loopback import assert_loopback_bind, reject_remote_requests

csrf = CSRFProtect()


def create_app(test_config: dict | None = None) -> Flask:
    # Werkzeug's debugger runs any Python typed into the browser. On an app with no login
    # that is remote code execution for whatever page reaches it, so debug mode never starts.
    if get_debug_flag():
        raise RuntimeError(
            "The admin does not run in debug mode. Unset FLASK_DEBUG and start it again."
        )

    app = Flask(__name__)
    app.config["TRUSTED_HOSTS"] = config.TRUSTED_HOSTS
    # CSRF tokens need a signing key, and there is no secret worth storing for one: a fresh
    # key per start only means a form left open across a restart has to be reloaded.
    app.config["SECRET_KEY"] = secrets.token_hex(32)
    # Set explicitly, never left to the browser default: no other site may ride this session.
    # `Secure` is left off because the admin is plain http on 127.0.0.1, where browsers
    # disagree on whether to keep a Secure cookie.
    app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
    app.config.update(test_config or {})

    csrf.init_app(app)
    app.before_request(reject_remote_requests)

    @app.get("/")
    def home():
        return render_template("index.html")

    return app


def serve(host: str = config.ADMIN_HOST, port: int = config.ADMIN_PORT) -> None:
    assert_loopback_bind(host)
    create_app().run(host=host, port=port, debug=False)
