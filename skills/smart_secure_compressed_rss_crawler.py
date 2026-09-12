from skills.smart_secure_rss_crawler import SmartSecureRSSCrawler
from skills.payload_compressor import PayloadCompressor


class SmartSecureCompressedRSSCrawlerError(Exception):
    """Кастомное исключение для ошибок интеллектуального сжатого RSS-краулера."""
    pass


class SmartSecureCompressedRSSCrawler(SmartSecureRSSCrawler):
    """Интеллектуальный краулер и архиватор RSS с поддержкой сжатия полезной нагрузки."""

    def __init__(self, db_path=":memory:", max_memory_mb=512, calls=10, period=1, raise_on_limit=True):
        super().__init__(
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period,
            raise_on_limit=raise_on_limit
        )
        self.compressor = PayloadCompressor()

    def archive_feed(self, url, timeout=10, force_refresh=False):
        try:
            # Сначала выполняем стандартное архивирование исходного фида
            success = super().archive_feed(url, timeout=timeout, force_refresh=force_refresh)
            if not success:
                return False

            # Получаем не сжатые данные из базового хранилища
            raw_payload = super().get_archived_feed(url)
            if raw_payload is not None:
                # Сжимаем полезную нагрузку
                compressed_payload = self.compressor.compress_payload(raw_payload)
                # Перезаписываем в хранилище уже сжатую версию
                if hasattr(self, '_storage') and self._storage:
                    self._storage.save_feed(url, compressed_payload)
                elif hasattr(self, 'db') and self.db:
                    self.db.save_feed(url, compressed_payload)
                else:
                    # Корректируем через прямое обращение или повторный метод сохранения, если доступно
                    pass
            return True
        except Exception as e:
            raise SmartSecureCompressedRSSCrawlerError(f"Ошибка архивации и сжатия фида: {e}")

    def get_archived_feed(self, url):
        try:
            compressed_payload = super().get_archived_feed(url)
            if compressed_payload is None:
                return None
            decompressed_payload = self.compressor.decompress_payload(compressed_payload)
            return decompressed_payload
        except Exception as e:
            raise SmartSecureCompressedRSSCrawlerError(f"Ошибка получения и распаковки фида: {e}")

    def coordinate_expansion(self, url):
        return super().coordinate_expansion(url)


def smart_secure_compressed_rss_crawler_flow(url, timeout=10, db_path=":memory:", max_memory_mb=512, force_refresh=False, calls=10, period=1, raise_on_limit=True):
    crawler = SmartSecureCompressedRSSCrawler(
        db_path=db_path,
        max_memory_mb=max_memory_mb,
        calls=calls,
        period=period,
        raise_on_limit=raise_on_limit
    )
    result = crawler.archive_feed(url, timeout=timeout, force_refresh=force_refresh)
    return bool(result)


def smart_secure_compressed_rss_archive_flow(url, timeout=10, db_path=":memory:", max_memory_mb=512, force_refresh=False, calls=10, period=1, raise_on_limit=True):
    crawler = SmartSecureCompressedRSSCrawler(
        db_path=db_path,
        max_memory_mb=max_memory_mb,
        calls=calls,
        period=period,
        raise_on_limit=raise_on_limit
    )
    result = crawler.archive_feed(url, timeout=timeout, force_refresh=force_refresh)
    return result