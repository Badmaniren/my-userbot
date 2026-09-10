import random


class file_cache:
    class FileCache:
        def get(self, key):
            return None


class http_ping:
    @staticmethod
    def check_endpoint(agent):
        pass


class cached_ping:
    @staticmethod
    def ping_and_cache(url):
        pass


class HeaderRotator:
    DEFAULT_USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    ]

    def __init__(self, use_cache=False):
        self.use_cache = use_cache
        self.user_agents = self._load_user_agents()

    def _load_user_agents(self):
        if self.use_cache:
            cache = file_cache.FileCache()
            data = cache.get("user_agents")
            if data and isinstance(data, (list, set, tuple)) and len(data) > 0:
                return list(data)
        return list(self.DEFAULT_USER_AGENTS)

    def get_headers(self):
        pool = self.user_agents if self.user_agents else self.DEFAULT_USER_AGENTS
        agent = random.choice(pool)
        return {
            "User-Agent": agent,
            "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    def validate_agent(self, agent):
        try:
            resp = http_ping.check_endpoint(agent)
            code = getattr(resp, "status_code", None)
            if code is None:
                code = getattr(resp, "status", None)
            if code is None and hasattr(resp, "getcode") and callable(resp.getcode):
                val = resp.getcode()
                if isinstance(val, int):
                    code = val
            if code is None:
                return False
            return code == 200
        except Exception:
            return False

    def sanitize_agent(self, agent):
        return agent.strip()

    def get_headers_with_ping(self, url):
        try:
            cached_ping.ping_and_cache(url)
        except Exception:
            pass
        return self.get_headers()