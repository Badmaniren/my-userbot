from html.parser import HTMLParser
from skills.http_ping import check_endpoint
from skills.cached_ping import ping_and_cache

class _HTMLLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'a':
            for attr, value in attrs:
                if attr.lower() == 'href' and value:
                    self.links.append(value)

class LinkExtractor:
    def extract(self, html_content: str, headers: dict = None, timeout: int = 5) -> list:
        if html_content is None:
            raise TypeError("html_content cannot be None")
        parser = _HTMLLinkParser()
        parser.feed(html_content)
        return parser.links

    def validate_link(self, url: str, timeout: int = 5) -> bool:
        try:
            response = check_endpoint(url, timeout)
            status = getattr(response, 'status_code', getattr(response, 'status', None))
            if status == 200:
                return True
            return False
        except Exception:
            return False

    def process_with_cache(self, url: str, timeout: int = 5) -> bool:
        try:
            response = ping_and_cache(url, timeout)
            status = getattr(response, 'status_code', getattr(response, 'status', None))
            if status == 200:
                return True
            return False
        except Exception:
            return False