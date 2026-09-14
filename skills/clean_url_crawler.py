from skills.url_cleaner import clean_url


class CleanUrlCrawlerError(Exception):
    """Кастомное исключение для CleanUrlCrawler."""
    pass


class CleanUrlCrawler:
    def process_url(self, url: str, timeout: float = 5.0) -> bool:
        if not isinstance(url, str):
            return False
        cleaned = clean_url(url)
        return bool(cleaned)

    def validate_crawled_link(self, url: str, timeout: float = 3.0) -> bool:
        if not isinstance(url, str):
            return False
        return url.startswith("http://") or url.startswith("https://")

    def extract_and_clean(self, html_content: str) -> list:
        if not isinstance(html_content, str):
            return []
        return []
