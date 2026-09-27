import unittest
import uuid
import random
import os
from skills.market_insider_anomaly_analyzer import MarketInsiderAnomalyAnalyzer, analyze_market_insider_anomalies

class TestMarketInsiderAnomalyAnalyzerIntegration(unittest.TestCase):
    def test_analyze_ticker_integration_real_skills(self):
        random_ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        random_volume = random.randint(10000, 999999)
        random_price = round(random.uniform(10.0, 1500.0), 2)
        
        stream_data = {
            "ticker": random_ticker,
            "volume": random_volume,
            "price": random_price,
            "timestamp": uuid.uuid4().hex
        }

        analyzer = MarketInsiderAnomalyAnalyzer()
        result = analyzer.analyze_ticker(random_ticker, stream_data)

        self.assertIsInstance(result, dict)
        self.assertIn("ticker", result)
        self.assertEqual(result["ticker"], random_ticker)
        self.assertIn("is_coordinated", result)
        self.assertIn("anomaly_data", result)
        self.assertIn("insider_alert_data", result)

    def test_analyze_market_insider_anomalies_file_generation(self):
        random_ticker = f"SEC_{uuid.uuid4().hex[:4].upper()}"
        random_exchange = f"EX_{uuid.uuid4().hex[:4].upper()}"
        random_price = round(random.uniform(50.0, 500.0), 2)
        
        raw_stream = {
            "price": random_price,
            "orders": random.randint(5, 50),
            "flag": uuid.uuid4().hex
        }

        result = analyze_market_insider_anomalies(ticker=random_ticker, exchange=random_exchange, raw_stream_data=raw_stream)

        self.assertIsInstance(result, dict)
        self.assertIn("correlation_id", result)
        correlation_id = result["correlation_id"]
        self.assertIsInstance(correlation_id, str)
        self.assertTrue(len(correlation_id) > 0)

        report_filename = f"insider_anomaly_report_{correlation_id}.json"
        self.assertTrue(os.path.exists(report_filename))

        try:
            if os.path.exists(report_filename):
                os.remove(report_filename)
        except OSError:
            pass

    def test_analyze_stream_integration(self):
        random_exchange = f"EXCH_{uuid.uuid4().hex[:5].upper()}"
        analyzer = MarketInsiderAnomalyAnalyzer()
        
        stream_result = analyzer.analyze_stream(random_exchange)

        self.assertIsInstance(stream_result, dict)
        self.assertIn("exchange", stream_result)
        self.assertEqual(stream_result["exchange"], random_exchange)
        self.assertIn("anomaly_items", stream_result)
        self.assertIn("insider_items", stream_result)

if __name__ == "__main__":
    unittest.main()