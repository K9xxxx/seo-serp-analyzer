from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

USER_AGENT = "Mozilla/5.0 (compatible; SeoAnalyzerBot/1.0)"
HEADERS = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}
MAX_BYTES = 5_000_000


class RobotsCache:
    def __init__(self):
        self._cache = {}

    def allowed(self, url):
        parsed = urlparse(url)
        host = parsed.netloc
        if host not in self._cache:
            rp = RobotFileParser()
            rp.set_url(f"{parsed.scheme}://{host}/robots.txt")
            try:
                rp.read()
            except Exception:
                pass
            self._cache[host] = rp
        return self._cache[host].can_fetch(USER_AGENT, url)


def fetch_page(url, session=None, robots=None, timeout=15):
    if robots is not None and not robots.allowed(url):
        return None, "blocked by robots.txt"

    sess = session or requests.Session()
    try:
        resp = sess.get(url, headers=HEADERS, timeout=timeout, stream=True)
        content_type = resp.headers.get("Content-Type", "")
        if "html" not in content_type.lower():
            return None, f"non-HTML content type: {content_type or 'unknown'}"
        if resp.status_code != 200:
            return None, f"HTTP {resp.status_code}"
        content = resp.content[:MAX_BYTES]
        encoding = resp.encoding or "utf-8"
        try:
            html = content.decode(encoding, errors="replace")
        except LookupError:
            html = content.decode("utf-8", errors="replace")
        return html, None
    except requests.RequestException as exc:
        return None, f"request failed: {exc.__class__.__name__}"
