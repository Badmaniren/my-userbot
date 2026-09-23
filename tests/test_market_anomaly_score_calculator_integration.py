import unittest
import os
import json
import uuid
import tempfile

from skills.market_anomaly_score_calculator import (
    MarketAnomalyScoreCalculator,
    process_anomaly_score_stream
)


class TestMarketAnomalyScoreCalculatorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_anomaly_storage_{uuid.uuid4().hex}.json")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_evaluate_market_data_integration_from_file(self):
        symbol = "BTC_USD"
        sample_data = {
            symbol: {
                "volume": 5000.0,
                "volume_history": [1000.0, 1100.0, 950.0, 1050.0, 1000.0],
                "price": 65000.0,
                "price_history": [60000.0, 60500.0, 59800.0, 60200.0, 60100.0],
                "volatility": 0.08,
                "volatility_history": [0.02, 0.021, 0.019, 0.02, 0.022]
            }
        }

        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(sample_data, f)

        calculator = MarketAnomalyScoreCalculator(storage_file=self.storage_file)
        result = calculator.evaluate_market_data(symbol)

        self.assertEqual(result["symbol"], symbol)
        self.assertIn("composite_score", result)
        self.assertIn("insider_event_probability", result)
        self.assertTrue(result["is_anomaly"])
        self.assertIn(result["severity"], ["HIGH", "CRITICAL"])

    def test_process_anomaly_score_stream_integration_list(self):
        stream_data = [
            {"symbol": "BTC", "volume_z": 2.5, "price_z": 1.5, "volatility_z": 2.0},
            {"symbol": "ETH", "volume_z": 0.1, "price_z": 0.2, "volatility_z": 0.1}
        ]

        results = process_anomaly_score_stream(stream_data, storage_file=self.storage_file)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["symbol"], "BTC")
        self.assertEqual(results[1]["symbol"], "ETH")
        self.assertTrue(results[0]["is_anomaly"])
        self.assertFalse(results[1]["is_anomaly"])


if __name__ == "__main__":
    unittest.main()
