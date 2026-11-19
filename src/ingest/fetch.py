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
TIMEOUT = 30
DELAY_SECONDS = 1.0  # pause between requests


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
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise FetchError(f"Download failed for '{source['id']}': {exc}") from exc

    path = raw_path(source, raw_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(resp.content)
    return path, dt.date.today().isoformat()
