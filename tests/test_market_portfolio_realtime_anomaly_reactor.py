import unittest
from unittest.mock import patch, MagicMock
import os
import json
import uuid
import random
import io

from skills.market_portfolio_realtime_anomaly_reactor import market_portfolio_realtime_anomaly_reactor

class TestMarketPortfolioRealtimeAnomalyReactor(unittest.TestCase):

    def setUp(self):
        self.random_ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        self.random_exchange = uuid.uuid4().hex
        self.random_output_path = f"tmp_output_{uuid.uuid4().hex}.json"
        self.random_session_id = uuid.uuid4().hex
        self.random_stream_source = f"stream_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.random_output_path):
            try:
                os.remove(self.random_output_path)
                os.rmdir(os.path.dirname(os.path.abspath(self.random_output_path)))
            except Exception:
                pass

    @patch("skills.market_portfolio_realtime_anomaly_reactor.market_portfolio_realtime_stream_ingestor")
    @patch("skills.market_portfolio_realtime_anomaly_reactor.market_anomaly_detector")
    def test_reactor_basic_execution(self, mock_anomaly_detector_module, mock_stream_ingestor):
        expected_ingest_res = {"status": "ingested", "id": uuid.uuid4().hex}
        mock_stream_ingestor.start_new.return_value = expected_ingest_res

        mock_detector_instance = MagicMock()
        expected_detection_res = {"is_anomaly": random.choice([True, False]), "score": random.random()}
        mock_detector_instance.detect.return_value = expected_detection_res
        mock_anomaly_detector_module.MarketAnomalyDetector.return_value = mock_detector_instance

        context = {"ticker": self.random_ticker, "session_id": self.random_session_id}
        result = market_portfolio_realtime_anomaly_reactor(
            context=context,
            stream_source=self.random_stream_source,
            exchange=self.random_exchange,
            ticker=self.random_ticker
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["ingest_result"], expected_ingest_res)
        self.assertEqual(result["detection_result"], expected_detection_res)
        mock_stream_ingestor.start_new.assert_called_once_with(context, self.random_stream_source)
        mock_detector_instance.detect.assert_called_once_with(self.random_ticker)
        mock_detector_instance.analyze_stream.assert_called_once_with(self.random_exchange)

    @patch("skills.market_portfolio_realtime_anomaly_reactor.market_portfolio_realtime_stream_ingestor")
    @patch("skills.market_portfolio_realtime_anomaly_reactor.market_anomaly_detector")
    def test_reactor_with_payload_and_output(self, mock_anomaly_detector_module, mock_stream_ingestor):
        expected_ingest_res = {"status": "ok", "bytes": random.randint(100, 999)}
        mock_stream_ingestor.start_new.return_value = expected_ingest_res

        mock_detector_instance = MagicMock()
        expected_detection_res = {"anomaly_detected": False, "ticker": self.random_ticker}
        mock_detector_instance.detect.return_value = expected_detection_res
        mock_anomaly_detector_module.MarketAnomalyDetector.return_value = mock_detector_instance

        payload = {"ticker": self.random_ticker, "session_id": self.random_session_id, "data": uuid.uuid4().hex}

        result = market_portfolio_realtime_anomaly_reactor(
            context=payload,
            stream_source=self.random_output_path,
            output_path=None
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["payload"], payload)
        self.assertTrue(os.path.exists(self.random_output_path))

        with open(self.random_output_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)
            self.assertEqual(file_data.get("session_id"), self.random_session_id)
            self.assertEqual(file_data.get("result", {}).get("detection_result"), expected_detection_res)

    @patch("skills.market_portfolio_realtime_anomaly_reactor.market_portfolio_realtime_stream_ingestor")
    @patch("skills.market_portfolio_realtime_anomaly_reactor.market_anomaly_detector")
    def test_reactor_default_ticker_fallback(self, mock_anomaly_detector_module, mock_stream_ingestor):
        mock_stream_ingestor.start_new.return_value = {}

        mock_detector_instance = MagicMock()
        mock_detector_instance.detect.return_value = {"status": "checked"}
        mock_anomaly_detector_module.MarketAnomalyDetector.return_value = mock_detector_instance

        result = market_portfolio_realtime_anomaly_reactor(
            context=None,
            stream_source=None,
            payload=None,
            ticker=None
        )

        self.assertEqual(result["status"], "success")
        mock_detector_instance.detect.assert_called_once_with("DEFAULT_TICKER")

    @patch("skills.market_portfolio_realtime_anomaly_reactor.market_portfolio_realtime_stream_ingestor")
    @patch("skills.market_portfolio_realtime_anomaly_reactor.market_anomaly_detector")
    def test_reactor_with_nested_payload_ticker(self, mock_anomaly_detector_module, mock_stream_ingestor):
        mock_stream_ingestor.start_new.return_value = {}

        mock_detector_instance = MagicMock()
        mock_detector_instance.detect.return_value = {"analyzed": True}
        mock_anomaly_detector_module.MarketAnomalyDetector.return_value = mock_detector_instance

        payload = {
            "ingest_data": {
                "ticker": self.random_ticker
            }
        }

        result = market_portfolio_realtime_anomaly_reactor(
            payload=payload
        )

        self.assertEqual(result["status"], "success")
        mock_detector_instance.detect.assert_called_once_with(self.random_ticker)

if __name__ == "__main__":
    unittest.main()