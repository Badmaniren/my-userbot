import xml.etree.ElementTree as ET
import requests


class SitemapParserError(Exception):
    """Исключение для ошибок парсинга Sitemap."""
    pass


class SitemapParser:
    def __init__(self):
        pass

    def parse(self, url: str, timeout: int = 5) -> list:
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            urls = []
            for elem in root.iter():
                if elem.tag.endswith('loc') and elem.text:
                    urls.append(elem.text.strip())
            return urls
        except Exception as e:
            if isinstance(e, requests.RequestException):
                raise requests.RequestException(str(e)) from e
            raise SitemapParserError(f"Failed to parse sitemap: {e}") from e

    def validate_sitemap(self, url: str, timeout: int = 5) -> bool:
        try:
            response = requests.head(url, timeout=timeout)
            if response.status_code == 200:
                return True
            response = requests.get(url, timeout=timeout)
            return response.status_code == 200
        except Exception:
            return False
