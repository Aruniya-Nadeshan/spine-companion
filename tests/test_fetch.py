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
