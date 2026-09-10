import random
from skills import http_ping, file_cache, clean_text

class HeadersRotator:
    DEFAULT_USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"
    ]

    def __init__(self, cache_enabled=False):
        self.cache_enabled = cache_enabled
        self.cache = None
        if self.cache_enabled:
            try:
                self.cache = file_cache.FileCache()
            except Exception:
                self.cache = None

    def get_random_user_agent(self):
        ua_list = self.DEFAULT_USER_AGENTS
        if self.cache and self.cache_enabled:
            try:
                cached_uas = self.cache.get("user_agents")
                if cached_uas and isinstance(cached_uas, list):
                    ua_list = cached_uas
            except Exception:
                pass
        return random.choice(ua_list)

    def get_sanitized_user_agent(self, raw_ua):
        if not isinstance(raw_ua, str):
            raw_ua = str(raw_ua)
        return clean_text.clean(raw_ua)

    def rotate_headers(self):
        ua = self.get_random_user_agent()
        return {
            "User-Agent": ua,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Connection": "keep-alive"
        }

    def validate_headers_against_target(self, url, timeout=5):
        if not isinstance(url, str) or not url.strip():
            raise ValueError("URL must be a non-empty string")
        if not isinstance(timeout, (int, float)) or timeout < 0:
            raise ValueError("Timeout must be a non-negative number")

        headers = self.rotate_headers()
        try:
            response = http_ping.check_endpoint(url, headers=headers, timeout=timeout)
            status = getattr(response, "status_code", None)
            if status is None:
                status = getattr(response, "status", None)
            
            if status == 200:
                return True
            return False
        except Exception:
            return False