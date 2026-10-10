import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import types

from skills.market_portfolio_realtime_anomaly_reactor_v2 import (
    RealtimeAnomalyReactor,
    reactor_entry_point
)

class TestRealtimeAnomalyReactor(unittest.TestCase):

    def setUp(self):
        self.stream_source = f"wss://exchange-{uuid.uuid4().hex[:8]}.io/stream"
        self.context_key = f"ctx_{uuid.uuid4().hex[:6]}"
        self.context_val = f"val_{uuid.uuid4().hex[:6]}"
        self.context = {self.context_key: self.context_val}
        self.payload = {
            "ticker": f"TICK_{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}",
            "price": round(random.uniform(10.0, 1500.0), 2),
            "volume": random.randint(100, 50000)
        }
        self.output_path = f"/tmp/{uuid.uuid4().hex}.json"

    def test_reactor_initialization_and_composition(self):
        reactor = RealtimeAnomalyReactor(stream_source=self.stream_source)
        self.assertEqual(reactor.stream_source, self.stream_source)
        self.assertIsNotNone(reactor.ingestor)
        self.assertIsNotNone(reactor.detector)

    @patch('skills.market_portfolio_realtime_anomaly_reactor_v2.market_portfolio_realtime_stream_ingestor')
    @patch('skills.market_portfolio_realtime_anomaly_reactor_v2.MarketAnomalyDetector')
    def test_process_realtime_stream_success(self, mock_detector_cls, mock_ingestor):
        expected_ingest_result = {
            "status": "success",
            "ingested_id": uuid.uuid4().hex,
            "data": self.payload
        }
        mock_ingestor.return_value = expected_ingest_result

        expected_detection_result = {
            "anomaly_detected": True,
            "severity": random.choice(["HIGH", "CRITICAL", "MEDIUM"]),
            "ticker": self.payload["ticker"]
        }
        mock_detector_instance = mock_detector_cls.return_value
        mock_detector_instance.analyze_stream.return_value = expected_detection_result

        reactor = RealtimeAnomalyReactor(stream_source=self.stream_source)
        result = reactor.process_stream_payload(self.payload, self.output_path)

        mock_ingestor.assert_called_once_with(self.payload, self.output_path)
        mock_detector_instance.analyze_stream.assert_called_once()
        
        self.assertEqual(result["ingestion"], expected_ingest_result)
        self.assertEqual(result["anomaly_analysis"], expected_detection_result)
        self.assertTrue(result["reactor_status"])

    @patch('skills.market_portfolio_realtime_anomaly_reactor_v2.start_new')
    @patch('skills.market_portfolio_realtime_anomaly_reactor_v2.MarketAnomalyDetector')
    def test_start_streaming_reactor_loop(self, mock_detector_cls, mock_start_new):
        stream_data_id = uuid.uuid4().hex
        mock_start_new.return_value = {
            "stream_id": stream_data_id,
            "state": "active",
            "metrics": {"ticks": random.randint(10, 100)}
        }

        mock_detector_instance = mock_detector_cls.return_value
        target_ticker = f"SYM_{random.randint(1000, 9999)}"
        mock_detector_instance.detect.return_value = {
            "ticker": target_ticker,
            "anomaly": False,
            "score": random.random()
        }

        reactor = RealtimeAnomalyReactor(stream_source=self.stream_source)
        run_res = reactor.start_live_monitoring(self.context)

        mock_start_new.assert_called_once_with(self.context, self.stream_source)
        mock_detector_instance.detect.assert_called()
        self.assertEqual(run_res["stream_id"], stream_data_id)
        self.assertIn("analysis", run_res)

    def test_reactor_entry_point_integration(self):
        with patch('skills.market_portfolio_realtime_anomaly_reactor_v2.market_portfolio_realtime_stream_ingestor') as mock_ingest, \
             patch('skills.market_portfolio_realtime_anomaly_reactor_v2.MarketAnomalyDetector') as mock_det:
            
            mock_ing.return_value = {"code": 200, "uuid": uuid.uuid4().hex}
            det_instance = mock_det.return_value
            det_instance.detect.return_value = {"status": "ok", "anomaly": True}

            entry_res = reactor_entry_point(self.payload, self.output_path)
            
            self.assertIsInstance(entry_res, dict)
            self.assertTrue(entry_res.get("processed"))
            mock_ing.assert_called_once()
            det_instance.detect.assert_called_once()

    @patch('skills.market_portfolio_realtime_anomaly_reactor_v2.market_portfolio_realtime_stream_ingestor')
    def test_stream_ingestor_failure_handling(self, mock_ingestor):
        mock_ingestor.side_effect = RuntimeError(f"Stream failure {uuid.uuid4().hex[:4]}")

        reactor = RealtimeAnomalyReactor(stream_source=self.stream_source)
        
        with self.assertRaises(RuntimeError):
            reactor.process_stream_payload(self.payload, self.output_path)

    def test_io_stream_byte_mocking(self):
        random_bytes = io.BytesIO(uuid.uuid4().bytes + b"stream_garbage_data")
        
        with patch('skills.market_portfolio_realtime_anomaly_reactor_v2.market_portfolio_realtime_stream_ingestor') as mock_ing, \
             patch('skills.market_portfolio_realtime_anomaly_reactor_v2.MarketAnomalyDetector') as mock_det:
            
            mock_ing.return_value = {"bytes_read": len(random_bytes.getvalue())}
            mock_det.return_value.analyze_stream.return_value = {"signal": "hold"}

            reactor = RealtimeAnomalyReactor(stream_source=self.stream_source)
            res = reactor.process_stream_payload({"stream_buffer": random_bytes.read()}, self.output_path)
            
            self.assertIn("bytes_read", res["ingestion"])
            self.assertEqual(res["anomaly_analysis"]["signal"], "hold")

if __name__ == '__main__':
    unittest.main()