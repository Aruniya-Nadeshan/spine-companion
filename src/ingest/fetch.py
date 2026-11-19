"""Download a source page into data/raw/.

Polite by design: identifies itself, checks robots.txt, uses a timeout,
and raises on any failure so a broken download can never pass silently.
Set INGEST_CONTACT (an email) in your environment so site owners can reach you.
"""
import datetime as dt
import os
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

CONTACT = os.environ.get("INGEST_CONTACT", "unset")
USER_AGENT = f"spine-companion-ingest/0.1 (student research project; contact: {CONTACT})"
HEADERS = {"User-Agent": USER_AGENT}
TIMEOUT = (10, 120)  # (connect, read) seconds; full-text XML can be large and slow
DELAY_SECONDS = 1.0  # pause between requests
MAX_ATTEMPTS = 3  # tries per download before giving up
RETRY_BACKOFF = 5  # seconds; multiplied by the attempt number


class FetchError(Exception):
    """Raised when a source cannot be downloaded."""


def allowed_by_robots(url):
    """Check the site's robots.txt for permission to fetch this URL."""
    parts = urlparse(url)
    robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    try:
        resp = requests.get(robots_url, headers=HEADERS, timeout=TIMEOUT)
    except requests.RequestException as exc:
        raise FetchError(f"Could not read {robots_url}: {exc}") from exc
    if resp.status_code >= 500:
        return False  # server error: be cautious
    if resp.status_code != 200:
        return True  # no usable robots.txt
    parser = RobotFileParser()
    parser.parse(resp.text.splitlines())
    return parser.can_fetch(USER_AGENT, url)


def _get_with_retries(url, source_id):
    """GET a URL, retrying timeouts, connection errors and 5xx server errors.

    Client errors (404, 403...) are not retried: asking again won't change them.
    """
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code >= 500:
                last_error = f"server error {resp.status_code}"
            else:
                resp.raise_for_status()  # raises on 4xx
                return resp
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_error = str(exc)
        except requests.RequestException as exc:
            raise FetchError(f"Download failed for '{source_id}': {exc}") from exc
        if attempt < MAX_ATTEMPTS:
            time.sleep(RETRY_BACKOFF * attempt)
    raise FetchError(
        f"Download failed for '{source_id}' after {MAX_ATTEMPTS} attempts: {last_error}")


def raw_path(source, raw_dir="data/raw"):
    """Where a source's downloaded original is stored."""
    ext = "xml" if source["format"] == "jats-xml" else "html"
    return Path(raw_dir) / f"{source['id']}.{ext}"


def fetch_source(source, raw_dir="data/raw"):
    """Download one source row. Returns (saved_path, access_date_iso).

    Web pages ("html") are only fetched if robots.txt allows it. Official
    machine-readable APIs ("jats-xml") are built for programmatic access, so
    the robots.txt check is not applied to them.
    """
    url = source["fetch_url"]
    if source["format"] == "html" and not allowed_by_robots(url):
        raise FetchError(f"robots.txt does not allow fetching {url}")
    time.sleep(DELAY_SECONDS)
    resp = _get_with_retries(url, source["id"])

    path = raw_path(source, raw_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(resp.content)
    return path, dt.date.today().isoformat()
