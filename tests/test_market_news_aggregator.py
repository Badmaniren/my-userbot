import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random

from skills import market_news_aggregator

class TestMarketNewsAggregator(unittest.TestCase):
    def test_aggregate_news(self):
        rand_url = f"http://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        rand_content = uuid.uuid4().hex.encode('utf-8')
        rand_id = random.randint(100, 999)

        mock_parser_instance = MagicMock()
        mock_parser_instance.fetch_feed.return_value = io.BytesIO(rand_content)

        mock_db_instance = MagicMock()
        mock_db_instance.save_article.side_effect = lambda c: rand_id if c == rand_content.decode('utf-8') else -1

        with patch('skills.market_news_aggregator.market_parser.ParserClient', return_value=mock_parser_instance):
            with patch('skills.market_news_aggregator.db_storage.DatabaseConnection', return_value=mock_db_instance):
                result = market_news_aggregator.aggregate_news(rand_url)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("id"), rand_id)
        self.assertEqual(result.get("source"), rand_url)

    def test_process_raw_stream_success(self):
        rand_url = f"http://{uuid.uuid4().hex}.net/{uuid.uuid4().hex}"
        payload = uuid.uuid4().bytes

        mock_parser_instance = MagicMock()
        mock_parser_instance.fetch_raw_stream.return_value = io.BytesIO(payload)

        with patch('skills.market_news_aggregator.market_parser.ParserClient', return_value=mock_parser_instance):
            length = market_news_aggregator.process_raw_stream(rand_url)

        self.assertEqual(length, len(payload))

    def test_process_raw_stream_empty(self):
        rand_url = f"http://{uuid.uuid4().hex}.org/{uuid.uuid4().hex}"

        mock_parser_instance = MagicMock()
        mock_parser_instance.fetch_raw_stream.return_value = io.BytesIO(b"")

        with patch('skills.market_news_aggregator.market_parser.ParserClient', return_value=mock_parser_instance):
            with self.assertRaises(ValueError):
                market_news_aggregator.process_raw_stream(rand_url)

    def test_aggregate_and_filter_news(self):
        valid_item_1 = {uuid.uuid4().hex: uuid.uuid4().hex}
        valid_item_2 = {uuid.uuid4().hex: random.randint(1, 100)}
        invalid_item_1 = None
        invalid_item_2 = uuid.uuid4().hex
        invalid_item_3 = 12345

        mixed_items = [valid_item_1, invalid_item_1, valid_item_2, invalid_item_2, invalid_item_3]

        filtered = market_news_aggregator.aggregate_and_filter_news(mixed_items)

        self.assertIn(valid_item_1, filtered)
        self.assertIn(valid_item_2, filtered)
        self.assertNotIn(invalid_item_1, filtered)
        self.assertNotIn(invalid_item_2, filtered)
        self.assertNotIn(invalid_item_3, filtered)
        self.assertEqual(len(filtered), 2)

if __name__ == '__main__':
    unittest.main()
