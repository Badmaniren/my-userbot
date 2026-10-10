import unittest
import tempfile
import os
import json
import uuid
import random
from skills.market_portfolio_realtime_anomaly_reactor import (
    market_portfolio_realtime_anomaly_reactor,
    MarketPortfolioRealtimeAnomalyReactor,
    process_realtime_anomaly_event,
    reactor_main_pipeline
)


class TestMarketPortfolioRealtimeAnomalyReactorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.session_id = f"sess_{uuid.uuid4().hex[:8]}"
        self.ticker = f"TICK_{random.randint(1000, 9999)}"
        self.exchange = f"EXCH_{uuid.uuid4().hex[:4].upper()}"
        self.price = round(random.uniform(10.0, 1500.0), 2)
        self.output_path = os.path.join(self.test_dir.name, f"report_{uuid.uuid4().hex[:6]}.json")

        self.payload = {
            "session_id": self.session_id,
            "ticker": self.ticker,
            "price": self.price,
            "volume": random.randint(100, 50000)
        }
        self.context = {
            "session_id": self.session_id,
            "ticker": self.ticker,
            "environment": "integration_test"
        }

    def tearDown(self):
        self.test_dir.cleanup()

    def test_process_stream_tick_integration(self):
        reactor = MarketPortfolioRealtimeAnomalyReactor(stream_source=self.exchange)
        context = {"session_id": self.session_id, "db_storage": None, "random_salt": uuid.uuid4().hex}

        result = reactor.process_stream_tick(context, self.ticker)

        self.assertIsInstance(result, dict)
        self.assertIn("anomaly_detected", result)
        self.assertEqual(result["ticker"], self.ticker)
        self.assertIn("ingest_result", result)
        self.assertIn("detection", result)

    def test_reactor_integration_flow(self):
        result = market_portfolio_realtime_anomaly_reactor(
            context=self.context,
            stream_source=self.output_path,
            payload=self.payload,
            exchange=self.exchange,
            ticker=self.ticker
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertIn("ingest_result", result)
        self.assertIn("detection_result", result)
        self.assertEqual(result.get("payload"), self.payload)

        self.assertTrue(os.path.exists(self.output_path))

        with open(self.output_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        self.assertEqual(file_data.get("session_id"), self.session_id)
        self.assertIn("result", file_data)
        self.assertEqual(file_data["result"]["status"], "success")

    def test_evaluate_exchange_feed_integration(self):
        reactor = MarketPortfolioRealtimeAnomalyReactor()
        payload = {
            "ticker": self.ticker,
            "exchange": self.exchange,
            "price": self.price,
            "nonce": uuid.uuid4().int
        }

        result = reactor.evaluate_exchange_feed(payload, self.output_path, self.exchange)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["exchange"], self.exchange)
        self.assertIn("anomalies", result)
        self.assertIn("ingest_audit", result)

    def test_process_realtime_anomaly_event_integration(self):
        payload = {
            "ticker": self.ticker,
            "exchange": self.exchange,
            "price": self.price,
            "event_id": str(uuid.uuid4())
        }

        result = process_realtime_anomaly_event(payload, self.output_path)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["ticker"], self.ticker)
        self.assertIn("anomaly_detected", result)
        self.assertIn("ingest_result", result)
        self.assertIn("detection", result)

    def test_reactor_main_pipeline_integration(self):
        stream_source = {
            "ticker": self.ticker,
            "exchange": self.exchange,
            "price": self.price,
            "batch_id": random.randint(100, 999)
        }

        result = reactor_main_pipeline(stream_source, self.output_path)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "pipeline_completed")
        self.assertIn("ingest", result)
        self.assertIn("anomalies", result)

        self.assertTrue(os.path.exists(self.output_path))
        self.assertGreater(os.path.getsize(self.output_path), 0)


if __name__ == "__main__":
    unittest.main()
