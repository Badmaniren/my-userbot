import requests
from skills.sitemap_parser import SitemapParser
from skills.url_cleaner import clean_url

class CleanSitemapParserError(Exception):
    """Исключение для ошибок парсинга sitemap."""
    pass

class CleanSitemapParser:
    def __init__(self):
        self._parser = SitemapParser()

    def parse(self, url, timeout=5):
        try:
            raw_urls = self._parser.parse(url, timeout=timeout)
            # Применяем clean_url к каждому элементу, чтобы нормализовать регистр и удалить UTM
            return [clean_url(u) for u in raw_urls]
        except requests.RequestException as e:
            raise CleanSitemapParserError(f"Network error: {e}")
        except Exception as e:
            raise CleanSitemapParserError(f"Parsing error: {e}")

    def validate_sitemap(self, url, timeout=5):
        try:
            result = self._parser.validate_sitemap(url, timeout=timeout)
            # Гарантируем возврат чистого bool, даже если парсер возвращает кортеж или иное
            return bool(result)
        except Exception:
            return False

    def parse_and_clean(self, url, timeout=5):
        return self.parse(url, timeout=timeout)

class CleanSitemapParserV2(CleanSitemapParser):
    """Класс-наследник для соответствия интеграционным тестам."""
    pass