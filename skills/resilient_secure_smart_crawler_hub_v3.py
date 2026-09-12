from skills import (
    resilient_secure_smart_crawler_hub_v2,
    headers_rotator,
    memory_profiler
)
from skills.resilient_secure_smart_crawler_hub_v2 import ResilientSecureSmartCrawlerHubV2
from skills.headers_rotator import HeadersRotator
from skills.memory_profiler import MemoryProfiler


class ResilientSecureSmartCrawlerHubV3Error(Exception):
    """Кастомное исключение для хаба версии 3."""
    pass


class ResilientSecureSmartCrawlerHubV3(ResilientSecureSmartCrawlerHubV2):
    """
    Отказоустойчивый и защищенный расширенный хаб интеллектуального краулинга v3,
    объединяющий координацию экспансии, ротацию заголовков и контроль памяти.
    """

    def __init__(self, db_path=":memory:", max_memory_mb=512, calls=10, period=60, raise_on_limit=True, **kwargs):
        super().__init__(db_path=db_path, **kwargs)
        self.max_memory_mb = max_memory_mb
        self.calls = calls
        self.period = period
        self.raise_on_limit = raise_on_limit
        
        # Композиция
        self.headers_rotator = HeadersRotator()
        self.memory_profiler = MemoryProfiler()

    def _check_memory(self):
        memory_profiler.assert_memory_limit(self.max_memory_mb, self.raise_on_limit)

    def coordinate_expansion(self, url, timeout):
        self._check_memory()
        try:
            return super().coordinate_expansion(url, timeout)
        except resilient_secure_smart_crawler_hub_v2.ResilientSecureSmartCrawlerHubError as e:
            raise ResilientSecureSmartCrawlerHubV3Error(str(e)) from e

    def coordinate_expansion_safe(self, url, timeout):
        self._check_memory()
        try:
            return super().coordinate_expansion_safe(url, timeout)
        except resilient_secure_smart_crawler_hub_v2.ResilientSecureSmartCrawlerHubError as e:
            raise ResilientSecureSmartCrawlerHubV3Error(str(e)) from e

    def validate_target_headers(self, url, timeout):
        self._check_memory()
        result = self.headers_rotator.validate_headers_against_target(url, timeout)
        return bool(result)

    def process_stream(self, url, timeout):
        self._check_memory()
        try:
            return super().process_stream(url, timeout)
        except resilient_secure_smart_crawler_hub_v2.ResilientSecureSmartCrawlerHubError as e:
            raise ResilientSecureSmartCrawlerHubV3Error(str(e)) from e