from skills.resilient_clean_compressed_sitemap_parser_v2 import (
    ResilientCleanCompressedSitemapParserV2 as ResilientCleanCompressedSitemapCrawler,
    ResilientCleanCompressedSitemapParserV2Error as ResilientCleanCompressedSitemapCrawlerError
)
import skills.resilient_clean_compressed_sitemap_parser_v2 as resilient_clean_compressed_sitemap_crawler

def resilient_clean_compressed_sitemap_crawl_flow(url: str, timeout: int = 5) -> list:
    crawler = ResilientCleanCompressedSitemapCrawler()
    return crawler.parse(url, timeout=timeout)
