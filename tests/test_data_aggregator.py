import unittest
from unittest.mock import patch, MagicMock
import io

from skills.data_aggregator import aggregate_data


class TestDataAggregator(unittest.TestCase):

    def test_aggregate_data_success(self):
        mock_raw_items = [
            {"title": "<b>Test Title 1</b>", "summary": "Some raw text &amp; symbols."},
            {"title": "Test Title 2", "summary": "Another text."}
        ]

        with patch('skills.data_aggregator.rss_parser.parse_feed') as mock_parse, \
             patch('skills.data_aggregator.clean_text.clean', side_effect=lambda x: x.replace("<b>", "").replace("</b>", "").replace("&amp;", "&")) as mock_clean:
            
            mock_parse.return_value = mock_raw_items
            
            result = aggregate_data("http://example.com/rss", timeout=5)
            
            self.assertTrue(isinstance(result, list))
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["title"], "Test Title 1")
            self.assertEqual(result[0]["summary"], "Some raw text & symbols.")
            mock_parse.assert_called_once_with("http://example.com/rss", timeout=5)

    def test_aggregate_data_empty_feed(self):
        with patch('skills.data_aggregator.rss_parser.parse_feed') as mock_parse:
            mock_parse.return_value = []
            
            result = aggregate_data("http://example.com/empty_rss")
            
            self.assertTrue(isinstance(result, list))
            self.assertEqual(len(result), 0)

    def test_aggregate_data_handles_parsing_exception(self):
        with patch('skills.data_aggregator.rss_parser.parse_feed') as mock_parse:
            mock_parse.side_effect = Exception("Network failure")
            
            result = aggregate_data("http://example.com/broken_rss")
            
            self.assertFalse(result)

    def test_aggregate_data_stream_io_integration(self):
        stream_mock = io.BytesIO(b"<rss><channel><item><title>Stream Item</title></item></channel></rss>")
        
        with patch('skills.data_aggregator.rss_parser.parse_feed') as mock_parse, \
             patch('skills.data_aggregator.clean_text.clean', return_value="Stream Item"):
            
            mock_parse.return_value = [{"title": stream_mock.read().decode('utf-8')}]
            
            result = aggregate_data("http://example.com/stream_rss")
            
            self.assertTrue(result)
            self.assertEqual(result[0]["title"], "Stream Item")

    def test_aggregate_data_raises_type_error_on_invalid_url(self):
        with self.assertRaises(TypeError):
            aggregate_data(None)