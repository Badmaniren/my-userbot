import unittest
from unittest.mock import patch
import os
import json
import uuid
import random
import io

from skills.market_portfolio_realtime_anomaly_reactor_bridge import (
    MarketPortfolioRealtimeAnomalyReactorBridge,
    market_portfolio_realtime_anomaly_reactor_bridge
)


class TestMarketPortfolioRealtimeAnomalyReactorBridge(unittest.TestCase):

    def setUp(self):
        self.rand_suffix = uuid.uuid4().hex[:8]
        self.ticker = f"TICK_{self.rand_suffix}"
        self.output_path = f"test_output_{self.rand_suffix}.json"
        self.stream_source = f"stream_{self.rand_suffix}"

    def tearDown(self):
        if os.path.exists(self.output_path):
            try:
                os.remove(self.output_path)
            except OSError:
                pass
        
        dir_name = os.path.dirname(os.path.abspath(self.output_path))
        if dir_name and os.path.exists(dir_name) and dir_name != os.getcwd():
            try:
                os.rmdir(dir_name)
            except OSError:
                pass

    def test_class_process_stream(self):
        reactor = MarketPortfolioRealtimeAnomalyReactorBridge(stream_source=self.stream_source)
        self.assertEqual(reactor.stream_source, self.stream_source)

        mock_reaction_id = uuid.uuid4().hex
        with patch("skills.market_anomaly_detector.MarketAnomalyDetector.detect") as mock_detect:
            mock_detect.return_value = {"reaction_id": mock_reaction_id}
            result = reactor.process_stream(self.ticker)
            self.assertEqual(result, mock_reaction_id)
            mock_detect.assert_called_once_with(self.ticker)

    @patch("skills.market_portfolio_realtime_anomaly_reactor_bridge.market_portfolio_realtime_stream_ingestor")
    @patch("skills.market_anomaly_detector.MarketAnomalyDetector.detect")
    def test_bridge_function_with_ticker(self, mock_detect, mock_ingestor):
        ingested_val = f"ingested_{uuid.uuid4().hex}"
        detection_val = f"detection_{uuid.uuid4().hex}"
        
        mock_ingestor.return_value = {"data": ingested_val}
        mock_detect.return_value = {"result": detection_val}

        payload = {"payload_key": uuid.uuid4().hex}
        result = market_portfolio_realtime_anomaly_reactor_bridge(
            payload_or_context=payload,
            output_path=self.output_path,
            ticker=self.ticker
        )

        self.assertIn("ingested_data", result)
        self.assertIn("detection_result", result)
        self.assertEqual(result["status"], "reacted")
        self.assertEqual(result["detection_result"]["result"], detection_val)

        self.assertTrue(os.path.exists(self.output_path))
        with open(self.output_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)
            self.assertEqual(file_data["status"], "reacted")
            self.assertEqual(file_data["detection_result"]["result"], detection_val)

    @patch("skills.market_anomaly_detector.MarketAnomalyDetector.detect")
    def test_bridge_function_payload_with_ticker(self, mock_detect):
        detection_val = random.randint(1000, 9999)
        mock_detect.return_value = {"code": detection_val}

        payload = {
            "ticker": self.ticker,
            "extra": uuid.uuid4().hex
        }

        result = market_portfolio_realtime_anomaly_reactor_bridge(
            payload_or_context=payload,
            output_path=self.output_path
        )

        self.assertEqual(result["status"], "reacted")
        self.assertEqual(result["detection_result"]["code"], detection_val)
        mock_detect.assert_called_once_with(self.ticker)

    @patch("skills.market_anomaly_detector.MarketAnomalyDetector.detect")
    def test_bridge_function_payload_with_detection_meta(self, mock_detect):
        detection_val = uuid.uuid4().hex
        mock_detect.return_value = {"id": detection_val}

        payload = {
            "detection_meta": {
                "ticker": self.ticker
            }
        }

        result = market_portfolio_realtime_anomaly_reactor_bridge(
            payload_or_context=payload,
            output_path=self.output_path
        )

        self.assertEqual(result["status"], "reacted")
        mock_detect.assert_called_once_with(self.ticker)

    @patch("skills.market_anomaly_detector.MarketAnomalyDetector.detect")
    def test_bridge_function_payload_unknown_ticker(self, mock_detect):
        mock_detect.return_value = {"status": "ok"}

        payload = {"random_field": uuid.uuid4().hex}

        result = market_portfolio_realtime_anomaly_reactor_bridge(
            payload_or_context=payload,
            output_path=self.output_path
        )

        self.assertEqual(result["status"], "reacted")
        mock_detect.assert_called_once_with("UNKNOWN")

    @patch("skills.market_portfolio_realtime_anomaly_reactor_bridge.market_portfolio_realtime_stream_ingestor")
    @patch("skills.market_anomaly_detector.MarketAnomalyDetector.detect")
    def test_bridge_function_ingestor_exception_fallback(self, mock_detect, mock_ingestor):
        mock_ingestor.side_effect = Exception("Ingestor failed")
        mock_detect.return_value = {"alert": True}

        payload = uuid.uuid4().hex
        result = market_portfolio_realtime_anomaly_reactor_bridge(
            payload_or_context=payload,
            output_path=self.output_path,
            ticker=self.ticker
        )

        self.assertEqual(result["ingested_data"], {"payload": payload})
        self.assertEqual(result["status"], "reacted")

    @patch("skills.market_anomaly_detector.MarketAnomalyDetector.detect")
    def test_bridge_directory_creation_failure_fallback(self, mock_detect):
        mock_detect.return_value = {"checked": True}
        
        invalid_dir_path = f"/invalid_restricted_path_{uuid.uuid4().hex}/output.json"
        
        with patch("os.makedirs", side_effect=OSError("Permission denied")):
            result = market_portfolio_realtime_anomaly_reactor_bridge(
                payload_or_context={"ticker": self.ticker},
                output_path=invalid_dir_path
            )
            self.assertEqual(result["status"], "reacted")