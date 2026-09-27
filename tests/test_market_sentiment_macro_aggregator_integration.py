import unittest
import uuid
import random
import os
from skills.market_sentiment_macro_aggregator import market_sentiment_macro_aggregator
from skills.db_storage import db_storage
from skills.market_parser import market_parser
from skills.market_news_sentiment_analyzer import market_news_sentiment_analyzer

class IntegrationTestMarketSentimentMacroAggregator(unittest.TestCase):
    def test_macro_aggregator_integration(self):
        random_symbol = f"TEST_{uuid.uuid4().hex[:6].upper()}"
        random_value = round(random.uniform(10.0, 1000.0), 2)
        
        parser_input = {
            "symbol": random_symbol,
            "metric_value": random_value,
            "source": "integration_test_stream"
        }
        
        parser_result = market_parser(parser_input)
        self.assertIsNotNone(parser_result)

        sentiment_input = {
            "symbol": random_symbol,
            "text": f"Market conditions for {random_symbol} are showing unexpected volatility and high sentiment shift."
        }
        sentiment_result = market_news_sentiment_analyzer(sentiment_input)
        self.assertIsNotNone(sentiment_result)

        aggregator_input = {
            "target_symbol": random_symbol,
            "parser_data": parser_result,
            "sentiment_data": sentiment_result,
            "include_macro": True
        }
        
        aggregation_result = market_sentiment_macro_aggregator(aggregator_input)
        
        self.assertIsInstance(aggregation_result, dict)
        self.assertIn("status", aggregation_result)
        self.assertEqual(aggregation_result.get("target_symbol"), random_symbol)

        db_payload = {
            "id": str(uuid.uuid4()),
            "symbol": random_symbol,
            "aggregated_data": aggregation_result
        }
        db_res = db_storage(db_payload)
        self.assertIsNotNone(db_res)

if __name__ == "__main__":
    unittest.main()