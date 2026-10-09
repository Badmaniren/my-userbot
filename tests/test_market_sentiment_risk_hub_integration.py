import unittest
import os
import uuid
import random
from skills.market_sentiment_risk_hub import MarketSentimentRiskHub, compute_market_risk_index, process_risk_stream

class TestMarketSentimentRiskHubIntegration(unittest.TestCase):
    def setUp(self):
        self.hub = MarketSentimentRiskHub()
        self.test_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.test_exchange = f"EXCH_{uuid.uuid4().hex[:6].upper()}"
        self.random_sentiment_text = f"Market crash anticipated due to random economic factors {uuid.uuid4().hex}"
        self.report_filename = f"report_{uuid.uuid4().hex}.txt"

    def tearDown(self):
        if os.path.exists(self.report_filename):
            try:
                os.remove(self.report_filename)
            except OSError:
                pass

    def test_evaluate_risk_integration(self):
        result = self.hub.evaluate_risk(ticker=self.test_ticker, exchange=self.test_exchange, news_snippet=self.random_sentiment_text)
        self.assertIsInstance(result, dict)
        self.assertIn("risk_index", result)
        self.assertIn("risk_score", result)
        self.assertIn("sentiment_score", result)
        self.assertIn("anomaly_score", result)
        self.assertGreaterEqual(result["risk_score"], 0.0)

    def test_compute_market_risk_index_integration(self):
        res = compute_market_risk_index(ticker=self.test_ticker, exchange=self.test_exchange)
        self.assertIsInstance(res, dict)
        self.assertIn("risk_index", res)

    def test_export_report_integration(self):
        export_status = self.hub.export_report(self.test_ticker, self.report_filename)
        self.assertTrue(export_status)
        self.assertTrue(os.path.exists(self.report_filename))
        with open(self.report_filename, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.test_ticker, content)

    def test_process_stream_integration(self):
        stream_data = f"Stream data packet {uuid.uuid4().hex}".encode('utf-8')
        from io import BytesIO
        stream_source = BytesIO(stream_data)
        stream_result = process_risk_stream(stream_source)
        self.assertIsInstance(stream_result, dict)
        self.assertEqual(stream_result.get("stream_status"), "PROCESSED")

if __name__ == "__main__":
    unittest.main()