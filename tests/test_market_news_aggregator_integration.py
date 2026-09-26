import unittest
import uuid
import random
import io
from skills import market_news_aggregator
import market_parser
import db_storage

class TestMarketNewsAggregatorIntegration(unittest.TestCase):

    def test_aggregate_news_integration(self):
        unique_content = f"Market News Update {uuid.uuid4()} - Rate cut expected: {random.randint(1, 100)}%"
        source_url = f"https://finance.example.com/feed/{uuid.uuid4()}"

        parser_client = market_parser.ParserClient()
        if hasattr(parser_client, 'set_mock_data'):
            parser_client.set_mock_data(source_url, unique_content)

        result = market_news_aggregator.aggregate_news(source_url)

        self.assertIsInstance(result, dict)
        self.assertIn("id", result)
        self.assertEqual(result["source"], source_url)
        self.assertIsNotNone(result["id"])

        db = db_storage.DatabaseConnection()
        if hasattr(db, 'get_article'):
            saved_content = db.get_article(result["id"])
            self.assertEqual(saved_content, unique_content)

    def test_process_raw_stream_integration(self):
        random_bytes = os_random_data = bytes([random.randint(0, 255) for _ in range(64)])
        stream_url = f"https://finance.example.com/stream/{uuid.uuid4()}"

        parser_client = market_parser.ParserClient()
        if hasattr(parser_client, 'set_mock_raw_stream'):
            parser_client.set_mock_raw_stream(stream_url, random_bytes)

        length = market_news_aggregator.process_raw_stream(stream_url)
        self.assertEqual(length, len(random_bytes))

    def test_aggregate_and_filter_news_integration(self):
        random_id_1 = str(uuid.uuid4())
        random_id_2 = str(uuid.uuid4())
        
        raw_items = [
            {"id": random_id_1, "title": "Bull Market Ahead"},
            None,
            {"id": random_id_2, "title": "Inflation Stays Low"},
            "invalid_item_string",
            12345
        ]

        filtered = market_news_aggregator.aggregate_and_filter_news(raw_items)

        self.assertIsInstance(filtered, list)
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]["id"], random_id_1)
        self.assertEqual(filtered[1]["id"], random_id_2)

if __name__ == "__main__":
    unittest.main()