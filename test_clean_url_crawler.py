import unittest
from unittest.mock import patch, MagicMock
from skills.clean_url_crawler import CleanUrlCrawler, clean_url_crawler_flow


class TestCleanUrlCrawler(unittest.TestCase):

    def setUp(self):
        self.crawler = CleanUrlCrawler()

    def test_init_composition(self):
        self.assertTrue(hasattr(self.crawler, 'link_extractor'))

    def test_extract_and_clean(self):
        html = '<a href="https://example.com/page?utm_source=test">Link</a>'
        with patch('skills.clean_url_crawler.LinkExtractor') as mock_le_cls, \
             patch('skills.clean_url_crawler.url_cleaner.clean_url') as mock_clean:
            
            mock_le_instance = mock_le_cls.return_value
            mock_le_instance.extract.return_value = ["https://example.com/page?utm_source=test"]
            
            crawler = CleanUrlCrawler()
            crawler.link_extractor = mock_le_instance
            mock_clean.return_value = "https://example.com/page"

            result = crawler.extract_and_clean(html)
            
            mock_le_instance.extract.assert_called_once_with(html)
            mock_clean.assert_called_once_with("https://example.com/page?utm_source=test")
            self.assertEqual(result, ["https://example.com/page"])

    def test_validate_crawled_link_success(self):
        url = "https://example.com"
        with patch.object(self.crawler.link_extractor, 'validate_link', return_value=True) as mock_validate:
            res = self.crawler.validate_crawled_link(url, timeout=5)
            mock_validate.assert_called_once_with(url, timeout=5)
            self.assertTrue(res)

    def test_validate_crawled_link_tuple_return(self):
        url = "https://example.com"
        with patch.object(self.crawler.link_extractor, 'validate_link', return_value=(True, "ok")) as mock_validate:
            res = self.crawler.validate_crawled_link(url, timeout=3)
            self.assertTrue(res)

    def test_validate_crawled_link_exception(self):
        url = "https://example.com"
        with patch.object(self.crawler.link_extractor, 'validate_link', side_effect=Exception("Error")):
            res = self.crawler.validate_crawled_link(url, timeout=3)
            self.assertFalse(res)

    def test_process_url_success(self):
        url = "https://example.com"
        with patch.object(self.crawler.link_extractor, 'process_with_cache', return_value=True) as mock_process:
            res = self.crawler.process_url(url, timeout=2)
            mock_process.assert_called_once_with(url, timeout=2)
            self.assertTrue(res)

    def test_process_url_tuple_return(self):
        url = "https://example.com"
        with patch.object(self.crawler.link_extractor, 'process_with_cache', return_value=(True, 200)) as mock_process:
            res = self.crawler.process_url(url, timeout=3)
            self.assertTrue(res)

    def test_process_url_exception(self):
        url = "https://example.com"
        with patch.object(self.crawler.link_extractor, 'process_with_cache', side_effect=Exception("Cache error")):
            res = self.crawler.process_url(url, timeout=3)
            self.assertFalse(res)

    def test_clean_url_crawler_flow_with_valid_links(self):
        html = '<a href="https://example.com/1">1</a><a href="https://example.com/2">2</a>'
        base_url = "https://example.com"
        
        with patch('skills.clean_url_crawler.CleanUrlCrawler.extract_and_clean', return_value=["https://example.com/1", "https://example.com/2"]) as mock_extract, \
             patch('skills.clean_url_crawler.CleanUrlCrawler.validate_crawled_link', side_effect=[True, False]) as mock_validate:
            
            result = clean_url_crawler_flow(html, base_url, timeout=4)
            
            mock_extract.assert_called_once_with(html)
            self.assertEqual(result, ["https://example.com/1"])

    def test_clean_url_crawler_flow_fallback_to_all(self):
        html = '<a href="https://example.com/1">1</a>'
        base_url = "https://example.com"
        
        with patch('skills.clean_url_crawler.CleanUrlCrawler.extract_and_clean', return_value=["https://example.com/1"]) as mock_extract, \
             patch('skills.clean_url_crawler.CleanUrlCrawler.validate_crawled_link', return_value=False) as mock_validate:
            
            result = clean_url_crawler_flow(html, base_url, timeout=3)
            
            mock_extract.assert_called_once_with(html)
            self.assertEqual(result, ["https://example.com/1"])


if __name__ == '__main__':
    unittest.main()