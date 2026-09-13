import requests
from bs4 import BeautifulSoup
from skills.url_cleaner import clean_url


class CleanUrlCrawlerError(Exception):
    """Кастомное исключение для CleanUrlCrawler."""
    pass


class CleanUrlCrawler:
    def __init__(self):
        pass

    def process_url(self, url: str, timeout: float = 5.0) -> bool:
        try:
            cleaned = clean_url(url)
            if not cleaned:
                return False
            response = requests.get(cleaned, timeout=timeout)
            return response.status_code == 200
        except Exception:
            return False

    def validate_crawled_link(self, url: str, timeout: float = 3.0) -> bool:
        try:
            cleaned = clean_url(url)
            if not cleaned:
                return False
            response = requests.head(cleaned, timeout=timeout)
            if response.status_code == 200:
                return True
            response = requests.get(cleaned, timeout=timeout)
            return response.status_code == 200
        except Exception:
            return False

    def extract_and_clean(self, html_content: str) -> list:
        if not html_content or not isinstance(html_content, str):
            return []
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            cleaned_links = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                cleaned = clean_url(href)
                if cleaned:
                    cleaned_links.append(cleaned)
            return cleaned_links
        except Exception:
            return []
