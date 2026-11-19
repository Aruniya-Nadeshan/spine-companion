import pytest

from src.ingest import fetch
from src.ingest.fetch import FetchError, fetch_source, raw_path


class FakeResponse:
    content = b"<article/>"
    status_code = 200

    def raise_for_status(self):
        pass


def source(fmt):
    return {"id": "demo", "format": fmt, "fetch_url": "https://example.org/x"}


def test_raw_path_extension_follows_format(tmp_path):
    assert raw_path(source("html"), tmp_path).name == "demo.html"
    assert raw_path(source("jats-xml"), tmp_path).name == "demo.xml"


def test_html_fetch_is_blocked_when_robots_disallows(monkeypatch, tmp_path):
    monkeypatch.setattr(fetch, "allowed_by_robots", lambda url: False)
    with pytest.raises(FetchError, match="robots.txt"):
        fetch_source(source("html"), tmp_path)


def test_api_fetch_skips_robots_check_and_saves_file(monkeypatch, tmp_path):
    monkeypatch.setattr(fetch, "allowed_by_robots", lambda url: pytest.fail("should not be called"))
    monkeypatch.setattr(fetch, "DELAY_SECONDS", 0)
    monkeypatch.setattr(fetch.requests, "get", lambda *a, **k: FakeResponse())
    path, accessed = fetch_source(source("jats-xml"), tmp_path)
    assert path.read_bytes() == b"<article/>"
    assert len(accessed) == 10


class HttpErrorResponse:
    def __init__(self, status):
        self.status_code = status
        self.content = b""

    def raise_for_status(self):
        raise fetch.requests.HTTPError(f"{self.status_code} error")


def no_waiting(monkeypatch):
    monkeypatch.setattr(fetch, "DELAY_SECONDS", 0)
    monkeypatch.setattr(fetch, "RETRY_BACKOFF", 0)


def test_timeouts_are_retried_then_succeed(monkeypatch, tmp_path):
    no_waiting(monkeypatch)
    calls = {"n": 0}

    def flaky(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] < 3:
            raise fetch.requests.Timeout("slow")
        return FakeResponse()

    monkeypatch.setattr(fetch.requests, "get", flaky)
    path, _ = fetch_source(source("jats-xml"), tmp_path)
    assert calls["n"] == 3
    assert path.exists()


def test_gives_up_after_max_attempts(monkeypatch, tmp_path):
    no_waiting(monkeypatch)
    calls = {"n": 0}

    def always_slow(*args, **kwargs):
        calls["n"] += 1
        raise fetch.requests.Timeout("slow")

    monkeypatch.setattr(fetch.requests, "get", always_slow)
    with pytest.raises(FetchError, match="after 3 attempts"):
        fetch_source(source("jats-xml"), tmp_path)
    assert calls["n"] == fetch.MAX_ATTEMPTS


def test_client_errors_are_not_retried(monkeypatch, tmp_path):
    no_waiting(monkeypatch)
    calls = {"n": 0}

    def not_found(*args, **kwargs):
        calls["n"] += 1
        return HttpErrorResponse(404)

    monkeypatch.setattr(fetch.requests, "get", not_found)
    with pytest.raises(FetchError, match="Download failed"):
        fetch_source(source("jats-xml"), tmp_path)
    assert calls["n"] == 1


def test_server_errors_are_retried(monkeypatch, tmp_path):
    no_waiting(monkeypatch)
    calls = {"n": 0}

    def unavailable(*args, **kwargs):
        calls["n"] += 1
        return HttpErrorResponse(503)

    monkeypatch.setattr(fetch.requests, "get", unavailable)
    with pytest.raises(FetchError, match="server error 503"):
        fetch_source(source("jats-xml"), tmp_path)
    assert calls["n"] == fetch.MAX_ATTEMPTS
