import unittest
import uuid
import random
import os
import tempfile
from typing import Dict, Any

from skills.market_portfolio_realtime_stream_ingestor import market_portfolio_realtime_stream_ingestor, start_new
from skills.market_anomaly_detector import MarketAnomalyDetector, market_anomaly_detector
from skills.market_portfolio_realtime_anomaly_reactor import reactor_main_pipeline, process_realtime_anomaly_event


class TestMarketPortfolioRealtimeAnomalyReactorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        self.exchange = f"EXCH_{uuid.uuid4().hex[:6].upper()}"
        self.random_price = round(random.uniform(10.0, 1500.0), 2)
        self.random_volume = random.randint(100, 50000)
        self.output_file = os.path.join(self.test_dir.name, f"anomaly_report_{uuid.uuid4().hex}.json")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_realtime_anomaly_reactor_composition(self):
        context_id = str(uuid.uuid4())
        stream_payload = {
            "context_id": context_id,
            "ticker": self.ticker,
            "exchange": self.exchange,
            "price": self.random_price,
            "volume": self.random_volume,
            "timestamp": uuid.uuid4().int
        }

        ingestor_result = market_portfolio_realtime_stream_ingestor(stream_payload, self.output_file)
        self.assertIsInstance(ingestor_result, dict)
        self.assertTrue(os.path.exists(self.output_file))

        detector_instance = MarketAnomalyDetector()
        detection_result = detector_instance.detect(self.ticker)
        
        if detection_result is None:
            detection_result = detector_instance.analyze_stream(self.exchange)

        stream_source = {
            "ticker": self.ticker,
            "exchange": self.exchange,
            "price": self.random_price
        }
        stream_start = start_new(context_id, stream_source)
        self.assertIsInstance(stream_start, dict)

        detector_func_result = market_anomaly_detector(stream_payload)
        self.assertIsNotNone(detector_func_result)

        reactor_output = process_realtime_anomaly_event(
            payload=stream_payload,
            output_path=self.output_file
        )
        self.assertIsInstance(reactor_output, dict)
        self.assertIn("status", reactor_output)

        pipeline_result = reactor_main_pipeline(
            stream_source=stream_source,
            output_path=self.output_file
        )
        self.assertIsInstance(pipeline_result, dict)
        self.assertTrue(os.path.exists(self.output_file))

        with open(self.output_file, "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertTrue(len(file_content) > 0)


if __name__ == "__main__":
    unittest.main()