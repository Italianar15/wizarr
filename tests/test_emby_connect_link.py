import requests

from app.services.media.emby import EmbyClient


class _Response:
    def __init__(self, status_code=204):
        self.status_code = status_code


def _emby_client():
    """Build an EmbyClient without running __init__ (mirrors existing tests)."""
    client = object.__new__(EmbyClient)
    client.post_calls = []

    def post(path, **kwargs):
        client.post_calls.append((path, kwargs))
        return _Response()

    client.post = post
    return client


def test_link_emby_connect_posts_expected_path_and_params():
    client = _emby_client()

    assert client.link_emby_connect("user-123", "person@example.com") is True
    assert client.post_calls == [
        (
            "/Users/user-123/Connect/Link",
            {"params": {"ConnectUsername": "person@example.com"}},
        )
    ]


def test_link_emby_connect_skips_blank_email():
    client = _emby_client()

    assert client.link_emby_connect("user-123", "") is False
    assert client.post_calls == []


def test_link_emby_connect_swallows_http_errors():
    client = _emby_client()

    def failing_post(path, **kwargs):
        response = requests.Response()
        response.status_code = 400
        raise requests.HTTPError("already linked", response=response)

    client.post = failing_post

    # Non-fatal by design: must return False, never raise.
    assert client.link_emby_connect("user-123", "person@example.com") is False


def test_connect_link_enabled_defaults_on(monkeypatch):
    monkeypatch.delenv("WIZARR_EMBY_CONNECT_LINK", raising=False)
    assert EmbyClient._connect_link_enabled() is True


def test_connect_link_enabled_respects_opt_out(monkeypatch):
    for value in ("false", "0", "no", "off", "FALSE"):
        monkeypatch.setenv("WIZARR_EMBY_CONNECT_LINK", value)
        assert EmbyClient._connect_link_enabled() is False

    for value in ("true", "1", "yes", "on"):
        monkeypatch.setenv("WIZARR_EMBY_CONNECT_LINK", value)
        assert EmbyClient._connect_link_enabled() is True
