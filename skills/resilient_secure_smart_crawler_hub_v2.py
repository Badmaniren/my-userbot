import requests
from skills.smart_crawler import SmartCrawler
from skills.headers_rotator import HeadersRotator


class ResilientSecureSmartCrawlerHubError(Exception):
    """Пользовательское исключение для хаба ResilientSecureSmartCrawlerHubV2."""
    pass


class ResilientSecureSmartCrawlerHubV2:
    def __init__(self, db_path=":memory:", max_memory_mb=100, calls=10, period=1.0, raise_on_limit=True):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.calls = calls
        self.period = period
        self.raise_on_limit = raise_on_limit

        # Инициализация SmartCrawler без передачи неожиданных аргументов в конструктор,
        # чтобы избежать TypeError, если у базового SmartCrawler другие параметры.
        try:
            self.crawler = SmartCrawler(db_path=self.db_path, max_memory_mb=self.max_memory_mb, calls=self.calls, period=self.period, raise_on_limit=self.raise_on_limit)
        except TypeError:
            try:
                self.crawler = SmartCrawler(db_path=self.db_path, max_memory_mb=self.max_memory_mb)
            except TypeError:
                try:
                    self.crawler = SmartCrawler()
                except Exception as e:
                    raise ResilientSecureSmartCrawlerHubError(f"Failed to initialize SmartCrawler: {e}") from e

        self.rotator = HeadersRotator()

    def coordinate_expansion(self, url, timeout=5):
        try:
            return self.crawler.coordinate_expansion(url, timeout=timeout)
        except Exception as e:
            raise ResilientSecureSmartCrawlerHubError(f"Coordinate expansion failed: {e}") from e

    def coordinate_expansion_safe(self, url, timeout=5):
        try:
            res = self.crawler.coordinate_expansion(url, timeout=timeout)
            return res if res is not None else False
        except Exception:
            return False

    def validate_target_headers(self, url, timeout=5):
        res = self.rotator.validate_headers_against_target(url, timeout=timeout)
        return bool(res)

    def process_stream(self, url, timeout=5):
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            return response.raw
        except Exception as e:
            raise ResilientSecureSmartCrawlerHubError(f"Process stream failed: {e}") from e