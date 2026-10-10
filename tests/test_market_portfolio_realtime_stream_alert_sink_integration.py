import unittest
import os
import uuid
import random
import tempfile
from skills.market_portfolio_realtime_stream_alert_sink import (
    market_portfolio_realtime_stream_alert_sink
)
from skills.market_portfolio_realtime_stream_ingestor import (
    market_portfolio_realtime_stream_ingestor,
    start_new
)
from skills.market_portfolio_alert_event_sink import (
    handle_portfolio_alert_event,
    route_and_sink_alerts
)

class TestMarketPortfolioRealtimeStreamAlertSinkIntegration(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.symbol = f"TEST_{uuid.uuid4().hex[:6].upper()}"
        self.stream_url = f"wss://stream.market.local/{uuid.uuid4().hex}"
        self.token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = os.path.join(self.test_dir.name, f"storage_{uuid.uuid4().hex}.json")
        self.output_path = os.path.join(self.test_dir.name, f"output_{uuid.uuid4().hex}.json")
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.threshold = round(random.uniform(1.0, 100.0), 2)
        self.channels = ["telegram", "webhook"]
        
    def tearDown(self):
        self.test_dir.cleanup()

    def test_realtime_stream_alert_sink_composition(self):
        payload = {
            "event_id": uuid.uuid4().hex,
            "symbol": self.symbol,
            "price": round(random.uniform(10.0, 1000.0), 2),
            "volume": random.randint(100, 10000),
            "timestamp": random.randint(1600000000, 1700000000)
        }

        ingest_context = {
            "session_id": uuid.uuid4().hex,
            "mode": "live"
        }
        
        ingest_result = start_new(ingest_context, self.stream_url)
        self.assertIsNotNone(ingest_result)

        processed_ingest = market_portfolio_realtime_stream_ingestor(payload, self.output_path)
        self.assertIsInstance(processed_ingest, dict)
        self.assertTrue(os.path.exists(self.output_path))

        sink_result = handle_portfolio_alert_event(
            symbol=self.symbol,
            url=self.stream_url,
            token=self.token,
            chat_id=self.chat_id,
            storage=self.storage_file,
            severity=self.severity,
            threshold=self.threshold,
            channels=self.channels
        )
        self.assertIsNotNone(sink_result)

        route_result = route_and_sink_alerts(
            storage=self.storage_file,
            symbol=self.symbol,
            url=self.stream_url,
            token=self.token,
            chat_id=self.chat_id,
            severity=self.severity,
            threshold=self.threshold,
            channels=self.channels
        )
        self.assertIsNotNone(route_result)

        module_output = market_portfolio_realtime_stream_alert_sink(
            payload=payload,
            output_path=self.output_path,
            storage=self.storage_file,
            url=self.stream_url,
            token=self.token,
            chat_id=self.chat_id,
            severity=self.severity,
            threshold=self.threshold,
            channels=self.channels
        )

        self.assertIsInstance(module_output, dict)
        self.assertTrue(os.path.exists(self.output_path))

if __name__ == '__main__':
    unittest.main()