from skills.link_extractor import LinkExtractor
from skills import url_cleaner

class CleanUrlCrawler:
    def __init__(self):
        self.link_extractor = LinkExtractor()

    def extract_and_clean(self, html: str) -> list:
        raw_links = self.link_extractor.extract(html)
        cleaned_links = []
        for link in raw_links:
            cleaned = url_cleaner.clean_url(link)
            cleaned_links.append(cleaned)
        return cleaned_links

    def validate_crawled_link(self, url: str, timeout: int = 5) -> bool:
        res = self.link_extractor.validate_link(url, timeout=timeout)
        if isinstance(res, tuple):
            return bool(res[0])
        return bool(res)

    def process_url(self, url: str, timeout: int = 3) -> bool:
        res = self.link_extractor.process_with_cache(url, timeout=timeout)
        if isinstance(res, tuple):
            return bool(res[0])
        return bool(res)


def clean_url_crawler_flow(raw_html: str, base_url: str, timeout: int = 5) -> list:
    crawler = CleanUrlCrawler()
    links = crawler.extract_and_clean(raw_html)
    valid_links = []
    for link in links:
        if crawler.validate_crawled_link(link, timeout=timeout):
            valid_links.append(link)
    return valid_links if valid_links else links