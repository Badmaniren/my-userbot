import unittest
import uuid
import random
import os
import tempfile
from typing import Dict, Any

from skills.market_portfolio_realtime_stream_ingestor import start_new as stream_ingestor_start, market_portfolio_realtime_stream_ingestor
from skills.market_anomaly_detector import MarketAnomalyDetector
from skills.market_portfolio_realtime_anomaly_reactor_bridge import (
    market_portfolio_realtime_anomaly_reactor_bridge
)

class TestMarketPortfolioRealtimeAnomalyReactorBridgeIntegration(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.ticker = f"TEST_{uuid.uuid4().hex[:6].upper()}"
        self.exchange = f"EX_{uuid.uuid4().hex[:4].upper()}"
        self.stream_source = f"wss://stream.mockexchange.local/{uuid.uuid4().hex}"
        self.output_file = os.path.join(self.test_dir.name, f"anomaly_event_{uuid.uuid4().hex}.json")
        
        self.random_price = round(random.uniform(10.0, 1500.0), 2)
        self.random_volume = random.randint(1000, 500000)
        
    def tearDown(self):
        self.test_dir.cleanup()

    def test_realtime_anomaly_reactor_composition_integration(self):
        context = {
            "session_id": uuid.uuid4().hex,
            "ticker": self.ticker,
            "exchange": self.exchange,
            "price": self.random_price,
            "volume": self.random_volume
        }

        ingestor_result = stream_ingestor_start(context, self.stream_source)
        self.assertIsInstance(ingestor_result, dict)

        payload = {
            "stream_id": ingestor_result.get("stream_id", uuid.uuid4().hex),
            "ticker": self.ticker,
            "exchange": self.exchange,
            "metrics": {
                "price": self.random_price,
                "volume": self.random_volume
            }
        }
        
        audited_stream = market_portfolio_realtime_stream_ingestor(payload, self.output_file)
        self.assertIsInstance(audited_stream, dict)
        self.assertTrue(os.path.exists(self.output_file))

        detector = MarketAnomalyDetector()
        detection_result = detector.detect(self.ticker)
        stream_analysis = detector.analyze_stream(self.exchange)
        
        self.assertIsNotNone(detection_result)
        self.assertIsNotNone(stream_analysis)

        bridge_payload = {
            "ingested_data": audited_stream,
            "detection_meta": {
                "ticker": self.ticker,
                "anomaly_score": random.uniform(0.0, 1.0),
                "is_anomaly": True
            }
        }
        
        bridge_output_path = os.path.join(self.test_dir.name, f"reactor_event_{uuid.uuid4().hex}.json")
        reaction_result = market_portfolio_realtime_anomaly_reactor_bridge(bridge_payload, bridge_output_path)

        self.assertIsInstance(reaction_result, dict)
        self.assertTrue(os.path.exists(bridge_output_path), "Модуль моста должен сформировать файл итогового события реакции.")

if __name__ == "__main__":
    unittest.main()