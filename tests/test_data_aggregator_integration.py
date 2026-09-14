import unittest
from skills.data_aggregator import aggregate_data
from skills.rss_parser import parse_feed
from skills.clean_text import clean

class TestDataAggregatorIntegration(unittest.TestCase):
    def test_aggregate_data_integration(self):
        test_url = "http://example.com/rss"
        result = aggregate_data(test_url)
        self.assertIsInstance(result, list)

if __name__ == "__main__":
    unittest.main()