from skills.resilient_secure_smart_crawler_hub_v4 import ResilientSecureSmartCrawlerHubV4
from skills.clean_compressed_db_storage import CleanCompressedDBStorage

class ResilientSecureSmartAggregatorV6Error(Exception):
    """Базовое исключение для агрегатора v6."""
    pass

class ResilientSecureSmartAggregatorV6:
    def __init__(self, db_path=":memory:", max_memory_mb=256, calls=10, period=1.0, raise_on_limit=True):
        self.hub = ResilientSecureSmartCrawlerHubV4(calls=calls, period=period)
        self.crawler_hub = self.hub  # Алиас для интеграционных тестов
        self.storage = CleanCompressedDBStorage(db_path=db_path)
        self.max_memory_mb = max_memory_mb
        self.raise_on_limit = raise_on_limit

    def coordinate_expansion(self, url, timeout):
        """
        Выполняет координацию расширения через хаб и сохраняет результат в БД.
        Исключения оборачиваются в ResilientSecureSmartAggregatorV6Error.
        """
        try:
            result = self.hub.coordinate_expansion(url, timeout=timeout)
        except Exception as e:
            raise ResilientSecureSmartAggregatorV6Error(f"Coordinate expansion failed: {e}") from e

        if result is not None:
            cleaned_url = self.storage.clean_target_url(url)
            # Если результат — это словарь с 'data', сохраняем его, иначе сохраняем строковое представление
            data_to_save = result.get("data", str(result)) if isinstance(result, dict) else str(result)
            cleaned_text = self.storage.clean_target_text(str(data_to_save))
            self.storage.save_cleaned_and_compressed_data(cleaned_url, cleaned_text)
        else:
            cleaned_url = self.storage.clean_target_url(url)
            cleaned_text = self.storage.clean_target_text("success")
            self.storage.save_cleaned_and_compressed_data(cleaned_url, cleaned_text)

        return result

    def coordinate_expansion_safe(self, url, timeout):
        """Безопасная проверка расширения, возвращает чистый bool."""
        return bool(self.hub.coordinate_expansion_safe(url, timeout=timeout))

    def validate_target_headers(self, url, timeout):
        """Валидация заголовков, возвращает чистый bool."""
        return bool(self.hub.validate_target_headers(url, timeout=timeout))

    def process_stream(self, url, timeout):
        """Обработка потока данных с пробросом исключений."""
        try:
            return self.hub.process_stream(url, timeout=timeout)
        except Exception as e:
            raise ResilientSecureSmartAggregatorV6Error(f"Stream processing failed: {e}") from e