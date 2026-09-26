import unittest
import uuid
import random
import os
from skills import market_news_aggregator
from skills import market_parser
from skills import db_storage

class TestMarketNewsAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_id = str(uuid.uuid4())
        self.random_source = f"source_{random.randint(1000, 9999)}_{self.test_id[:8]}"
        self.random_title = f"Market Update {random.randint(10000, 99999)}"
        self.db_path = "test_market_news.db"

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_news_aggregation_and_storage_integration(self):
        raw_feed_data = {
            "source_id": self.random_source,
            "title": self.random_title,
            "content": f"Detailed financial report content for ID {self.test_id}.",
            "timestamp": random.randint(1600000000, 1900000000)
        }

        parsed_data = market_parser.parse_feed(raw_feed_data)
        self.assertIsNotNone(parsed_data)

        aggregation_result = market_news_aggregator.aggregate_and_filter_news([parsed_data])
        self.assertIsInstance(aggregation_result, list)
        
        saved_records = db_storage.persist_news_batch(aggregation_result, db_uri=self.db_path)
        
        fetched_record = db_storage.get_news_by_title(self.random_title, db_uri=self.db_path)
        self.assertIsNotNone(fetched_record)
        self.assertEqual(fetched_record.get("title"), self.random_title)
        self.assertIn(self.test_id[:8], fetched_record.get("content", ""))

if __name__ == "__main__":
    unittest.main()