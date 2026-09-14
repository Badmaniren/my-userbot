from skills.smart_crawler import SmartCrawler as CleanUrlCrawler

class CleanUrlCrawlerError(Exception):
    """Исключение для ошибок краулера URL."""
    pass


def clean_url_crawler_flow(raw_html: str, base_url: str, timeout: int = 5) -> list:
    crawler = CleanUrlCrawler()
    return crawler.coordinate_expansion(base_url, timeout=timeout)
