import unittest
from unittest.mock import patch, MagicMock
import os
import json
import uuid
import random
import io

from skills.market_portfolio_realtime_anomaly_reactor import (
    market_portfolio_realtime_anomaly_reactor,
    MarketPortfolioRealtimeAnomalyReactor,
    process_realtime_anomaly_event,
    reactor_main_pipeline,
    market_portfolio_realtime_anomaly_reactor_main
)


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
            except Exception:
                pass

    @patch("skills.market_portfolio_realtime_anomaly_reactor.market_portfolio_realtime_stream_ingestor")
    @patch("skills.market_portfolio_realtime_anomaly_reactor.MarketAnomalyDetector")
    def test_reactor_basic_execution(self, mock_anomaly_detector_class, mock_stream_ingestor):
        expected_ingest_res = {"status": "ingested", "id": uuid.uuid4().hex}
        mock_stream_ingestor.start_new.return_value = expected_ingest_res

        mock_detector_instance = MagicMock()
        expected_detection_res = {"is_anomaly": random.choice([True, False]), "score": random.random()}
        mock_detector_instance.detect.return_value = expected_detection_res
        mock_anomaly_detector_class.return_value = mock_detector_instance

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
    @patch("skills.market_portfolio_realtime_anomaly_reactor.MarketAnomalyDetector")
    def test_reactor_with_payload_and_output(self, mock_anomaly_detector_class, mock_stream_ingestor):
        expected_ingest_res = {"status": "ok", "bytes": random.randint(100, 999)}
        mock_stream_ingestor.start_new.return_value = expected_ingest_res

        mock_detector_instance = MagicMock()
        expected_detection_res = {"anomaly_detected": False, "ticker": self.random_ticker}
        mock_detector_instance.detect.return_value = expected_detection_res
        mock_anomaly_detector_class.return_value = mock_detector_instance

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
    @patch("skills.market_portfolio_realtime_anomaly_reactor.MarketAnomalyDetector")
    def test_reactor_default_ticker_fallback(self, mock_anomaly_detector_class, mock_stream_ingestor):
        mock_stream_ingestor.start_new.return_value = {}

        mock_detector_instance = MagicMock()
        mock_detector_instance.detect.return_value = {"status": "checked"}
        mock_anomaly_detector_class.return_value = mock_detector_instance

        result = market_portfolio_realtime_anomaly_reactor(
            context=None,
            stream_source=None,
            payload=None,
            ticker=None
        )

        self.assertEqual(result["status"], "success")
        mock_detector_instance.detect.assert_called_once_with("DEFAULT_TICKER")

    @patch("skills.market_portfolio_realtime_anomaly_reactor.market_portfolio_realtime_stream_ingestor")
    @patch("skills.market_portfolio_realtime_anomaly_reactor.MarketAnomalyDetector")
    def test_reactor_class_process_stream_tick(self, mock_anomaly_detector_class, mock_stream_ingestor):
        mock_ingest = {"status": "ok"}
        mock_stream_ingestor.start_new.return_value = mock_ingest

        mock_detector_instance = MagicMock()
        mock_detection = {"is_anomaly": True, "score": 0.95}
        mock_detector_instance.detect.return_value = mock_detection
        mock_anomaly_detector_class.return_value = mock_detector_instance

        reactor = MarketPortfolioRealtimeAnomalyReactor(stream_source=self.random_stream_source)
        res = reactor.process_stream_tick({"session_id": self.random_session_id}, self.random_ticker)

        self.assertTrue(res["anomaly_detected"])
        self.assertEqual(res["ticker"], self.random_ticker)
        self.assertEqual(res["ingest_result"], mock_ingest)
        self.assertEqual(res["detection"], mock_detection)

    @patch("skills.market_portfolio_realtime_anomaly_reactor.market_portfolio_realtime_stream_ingestor")
    @patch("skills.market_portfolio_realtime_anomaly_reactor.MarketAnomalyDetector")
    def test_evaluate_exchange_feed(self, mock_anomaly_detector_class, mock_stream_ingestor):
        mock_audit = {"audit_id": uuid.uuid4().hex, "status": "audited"}
        mock_stream_ingestor.market_portfolio_realtime_stream_ingestor.return_value = mock_audit

        mock_detector_instance = MagicMock()
        mock_anomalies = [{"anomaly_id": uuid.uuid4().hex, "severity": "HIGH"}]
        mock_detector_instance.analyze_stream.return_value = mock_anomalies
        mock_anomaly_detector_class.return_value = mock_detector_instance

        payload = {"ticker": self.random_ticker, "price": 100}
        reactor = MarketPortfolioRealtimeAnomalyReactor()
        res = reactor.evaluate_exchange_feed(payload, self.random_output_path, self.random_exchange)

        self.assertEqual(res["exchange"], self.random_exchange)
        self.assertEqual(res["anomalies"], mock_anomalies)
        self.assertEqual(res["ingest_audit"], mock_audit)

    def test_process_raw_bytes_stream(self):
        rand_data = b"sample_binary_bytes"
        bio = io.BytesIO(rand_data)

        reactor = MarketPortfolioRealtimeAnomalyReactor()
        read_bytes = reactor._process_raw_bytes_stream(bio)

        self.assertEqual(read_bytes, rand_data)

    @patch("skills.market_portfolio_realtime_anomaly_reactor.market_portfolio_realtime_stream_ingestor")
    @patch("skills.market_portfolio_realtime_anomaly_reactor.MarketAnomalyDetector")
    def test_process_realtime_anomaly_event(self, mock_anomaly_detector_class, mock_stream_ingestor):
        payload = {"ticker": self.random_ticker, "exchange": self.random_exchange, "value": 12.34}
        mock_ingest = {"status": "ok"}
        mock_detection = {"is_anomaly": True}

        mock_stream_ingestor.market_portfolio_realtime_stream_ingestor.return_value = mock_ingest
        mock_detector_instance = MagicMock()
        mock_detector_instance.detect.return_value = mock_detection
        mock_anomaly_detector_class.return_value = mock_detector_instance

        res = process_realtime_anomaly_event(payload, self.random_output_path)

        self.assertEqual(res["status"], "success")
        self.assertTrue(res["anomaly_detected"])
        self.assertEqual(res["ticker"], self.random_ticker)
        self.assertEqual(res["ingest_result"], mock_ingest)
        self.assertEqual(res["detection"], mock_detection)

    @patch("skills.market_portfolio_realtime_anomaly_reactor.market_portfolio_realtime_stream_ingestor")
    @patch("skills.market_portfolio_realtime_anomaly_reactor.MarketAnomalyDetector")
    def test_reactor_main_pipeline(self, mock_anomaly_detector_class, mock_stream_ingestor):
        stream_source = {"ticker": self.random_ticker, "exchange": self.random_exchange, "price": 150.0}
        mock_ingest = {"ingested": True}
        mock_anomalies = []

        mock_stream_ingestor.market_portfolio_realtime_stream_ingestor.return_value = mock_ingest
        mock_detector_instance = MagicMock()
        mock_detector_instance.analyze_stream.return_value = mock_anomalies
        mock_anomaly_detector_class.return_value = mock_detector_instance

        res = reactor_main_pipeline(stream_source, self.random_output_path)

        self.assertEqual(res["status"], "pipeline_completed")
        self.assertEqual(res["ingest"], mock_ingest)
        self.assertEqual(res["anomalies"], mock_anomalies)
        self.assertTrue(os.path.exists(self.random_output_path))


if __name__ == "__main__":
    unittest.main()
