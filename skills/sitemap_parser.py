import requests
import xml.etree.ElementTree as ET


class SitemapParserError(Exception):
    pass


class SitemapParser:
    def parse(self, url: str, timeout: int = 5) -> list:
        try:
            resp = requests.get(url, timeout=timeout)
            if resp.status_code != 200:
                raise SitemapParserError(f"HTTP {resp.status_code}")
            root = ET.fromstring(resp.content)
            urls = []
            for elem in root.iter():
                if elem.tag.endswith('loc') and elem.text:
                    urls.append(elem.text.strip())
            return urls
        except Exception as e:
            raise SitemapParserError(str(e)) from e

    def validate_sitemap(self, url: str, timeout: int = 5) -> bool:
        try:
            urls = self.parse(url, timeout=timeout)
            return bool(urls)
        except Exception:
            return False
