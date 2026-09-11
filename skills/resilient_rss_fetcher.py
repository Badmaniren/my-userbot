import logging
from skills.db_storage import DBStorage
from skills.headers_rotator import HeadersRotator
from skills.rate_limiter import RateLimiter, RateLimitExceeded
from skills.cached_rss_archiver import CachedRSSArchiver

logger = logging.getLogger(__name__)


class ResilientFetcherError(Exception):
    """Базовое исключение для ошибок отказоустойчивого загрузчика RSS."""
    pass


class ResilientRSSFetcher:
    """
    Комбинированный модуль для отказоустойчивой загрузки, ротации заголовков,
    ограничения частоты запросов и кэширования RSS фидов.
    """

    def __init__(
        self,
        db_path=":memory:",
        max_memory_mb=512,
        calls=10,
        period=1.0,
        raise_on_limit=True
    ):
        self.db = DBStorage(db_path=db_path)
        self.headers_rotator = HeadersRotator()
        self.rate_limiter = RateLimiter(calls=calls, period=period)
        self.archiver = CachedRSSArchiver(db_path=db_path)
        self.max_memory_mb = max_memory_mb
        self.raise_on_limit = raise_on_limit

    def _validate_input(self, url: str, timeout: float) -> None:
        if not url or not isinstance(url, str):
            raise ValueError("URL должен быть непустой строкой")
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("Timeout должен быть положительным числом")

    def fetch(self, url: str, timeout=5, force_refresh=False):
        """Загружает RSS фид с применением ограничения частоты, ротации заголовков и кэширования."""
        self._validate_input(url, timeout)

        try:
            self.rate_limiter.acquire()
        except RateLimitExceeded:
            raise
        except Exception as e:
            if self.raise_on_limit and isinstance(e, RateLimitExceeded):
                raise
            raise ResilientFetcherError(f"Ошибка ограничителя частоты: {e}") from e

        try:
            headers = self.headers_rotator.rotate_headers()
            
            if hasattr(self.headers_rotator, 'validate_headers_against_target'):
                try:
                    validation_res = self.headers_rotator.validate_headers_against_target(url, headers, timeout=timeout)
                except TypeError:
                    validation_res = self.headers_rotator.validate_headers_against_target(url, headers)
                
                if isinstance(validation_res, tuple):
                    valid = bool(validation_res[0])
                else:
                    valid = bool(validation_res)

                if not valid:
                    raise ResilientFetcherError("Валидация заголовков против цели не прошла")

            result = self.archiver.archive_feed(url, timeout, force_refresh=force_refresh)
            return result
        except RateLimitExceeded:
            raise
        except ResilientFetcherError:
            raise
        except Exception as e:
            raise ResilientFetcherError(f"Ошибка при получении RSS фида: {e}") from e

    def get_cached(self, url: str):
        """Возвращает кэшированный фид по URL."""
        try:
            return self.archiver.get_archived_feed(url)
        except Exception:
            return None

    def fetch_and_archive(self, url: str, timeout=5, force_refresh=False):
        """Интеграционный метод для загрузки и архивации."""
        return self.fetch(url, timeout=timeout, force_refresh=force_refresh)

    def get_cached_fetch(self, url: str):
        """Интеграционный метод для получения кэша."""
        return self.get_cached(url)