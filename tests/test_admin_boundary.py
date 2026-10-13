"""The admin has no login, so "laptop only" is its whole security boundary."""

import pytest

from admin.app import create_app, serve


@pytest.fixture
def client():
    return create_app({"TESTING": True}).test_client()


def test_home_page_loads_on_the_laptop(client):
    assert client.get("/").status_code == 200


@pytest.mark.parametrize("host", ["0.0.0.0", "192.168.1.10", "::"])
def test_serve_refuses_an_address_other_devices_can_reach(host):
    with pytest.raises(RuntimeError, match="127.0.0.1 only"):
        serve(host=host)


def test_refuses_to_start_in_debug_mode(monkeypatch):
    monkeypatch.setenv("FLASK_DEBUG", "1")
    with pytest.raises(RuntimeError, match="debug mode"):
        create_app()


def test_request_from_another_device_is_rejected(client):
    """Covers the app being started some other way on a network-facing address."""
    response = client.get("/", environ_overrides={"REMOTE_ADDR": "192.168.1.10"})
    assert response.status_code == 403


def test_request_naming_another_host_is_rejected(client):
    """A hostile page that points its own domain at 127.0.0.1 sends its own Host header."""
    response = client.get("/", headers={"Host": "evil.example"})
    assert response.status_code == 400


def test_no_other_site_is_allowed_to_read_responses(client):
    """No CORS header at all: the browser then blocks every cross-origin read."""
    response = client.get("/", headers={"Origin": "https://evil.example"})
    assert "Access-Control-Allow-Origin" not in response.headers


def test_session_cookie_is_same_site_strict_and_hidden_from_scripts():
    app = create_app({"TESTING": True})
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Strict"
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
