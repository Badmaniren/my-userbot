import xml.etree.ElementTree as ET
import requests


class SitemapParserError(Exception):
    """Исключение при ошибках загрузки или парсинга sitemap."""
    pass


class SitemapParser:
    def __init__(self):
        pass

    def is_sitemap_index(self, content: bytes) -> bool:
        if not content or not content.strip():
            return False
        try:
            root = ET.fromstring(content)
            tag = root.tag.lower()
            return tag.endswith("sitemapindex") or "sitemapindex" in tag
        except ET.ParseError:
            return False

    def extract_links(self, content: bytes) -> list[str]:
        if not content or not content.strip():
            return []
        try:
            root = ET.fromstring(content)
        except ET.ParseError as err:
            raise SitemapParserError(f"Failed to parse XML: {err}") from err

        links = []
        for elem in root.iter():
            if elem.tag.lower().endswith("loc") and elem.text:
                link = elem.text.strip()
                if link:
                    links.append(link)
        return links

    def parse(self, url: str, timeout: int = 10) -> list[str]:
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code != 200:
                raise SitemapParserError(f"Request failed with status code {response.status_code}")
        except SitemapParserError:
            raise
        except Exception as err:
            raise SitemapParserError(f"Network error while fetching {url}: {err}") from err

        return self.extract_links(response.content)

    def validate_sitemap(self, url: str, timeout: int = 10) -> bool:
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            return response.status_code == 200
        except Exception:
            return False


def parse_sitemap(url: str, timeout: int = 10) -> list[str]:
    parser = SitemapParser()
    return parser.parse(url, timeout=timeout)
