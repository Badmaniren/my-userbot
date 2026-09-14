from skills.resilient_clean_compressed_sitemap_parser import (
    ResilientCleanCompressedSitemapParser,
    ResilientCleanCompressedSitemapParserError,
)


class ResilientCleanCompressedSitemapCrawlerError(ResilientCleanCompressedSitemapParserError):
    pass


class ResilientCleanCompressedSitemapCrawler(ResilientCleanCompressedSitemapParser):
    def crawl(self, url: str, timeout: int = 5):
        return self.parse(url, timeout)

    def crawl_and_clean(self, url: str, timeout: int = 5):
        return self.parse_and_clean(url, timeout)
