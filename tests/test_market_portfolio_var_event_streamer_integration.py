import unittest
import uuid
import random
import os
from skills.market_portfolio_var_event_streamer import run_var_event_streamer
from skills.db_storage import save_stream_record, get_stream_record
from skills.market_portfolio_collector_agent import collect_market_data

class TestMarketPortfolioVarEventStreamerIntegration(unittest.TestCase):
    def test_var_event_streamer_real_integration(self):
        unique_symbol = f"TEST_{uuid.uuid4().hex[:8].upper()}"
        random_price = round(random.uniform(10.0, 1000.0), 2)
        random_volume = random.randint(100, 10000)

        raw_data = collect_market_data(symbol=unique_symbol, price=random_price, volume=random_volume)
        self.assertIsNotNone(raw_data)

        stream_id = str(uuid.uuid4())
        confidence_level = round(random.uniform(0.90, 0.99), 4)

        stream_result = run_var_event_streamer(
            stream_id=stream_id,
            symbol=unique_symbol,
            confidence=confidence_level,
            payload=raw_data
        )

        self.assertIsInstance(stream_result, dict)
        self.assertEqual(stream_result.get("stream_id"), stream_id)
        self.assertEqual(stream_result.get("symbol"), unique_symbol)
        self.assertIn("var_metric", stream_result)

        saved_status = save_stream_record(stream_result)
        self.assertTrue(saved_status)

        persisted_data = get_stream_record(stream_id)
        self.assertIsNotNone(persisted_data)
        self.assertEqual(persisted_data.get("stream_id"), stream_id)
        self.assertEqual(persisted_data.get("symbol"), unique_symbol)
        self.assertEqual(persisted_data.get("var_metric"), stream_result.get("var_metric"))

if __name__ == "__main__":
    unittest.main()