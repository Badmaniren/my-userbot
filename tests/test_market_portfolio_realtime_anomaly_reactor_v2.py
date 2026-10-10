import unittest
from unittest.mock import patch
import uuid
import random
import os
import tempfile

from skills.market_portfolio_realtime_anomaly_reactor_v2 import (
    RealtimeAnomalyReactor,
    reactor_entry_point,
    market_portfolio_realtime_anomaly_reactor_v2
)


class TestRealtimeAnomalyReactor(unittest.TestCase):

    def setUp(self):
        self.stream_source_val = f"wss://exchange-{uuid.uuid4().hex[:8]}.io/stream"
        self.reactor = RealtimeAnomalyReactor(stream_source=self.stream_source_val)
        self.payload = {
            "ticker": f"TICK-{uuid.uuid4().hex[:4].upper()}",
            "price": round(random.uniform(10.0, 1500.0), 2),
            "volume": random.randint(100, 50000),
            "stream_source": self.stream_source_val
        }
        self.output_path = os.path.join(tempfile.gettempdir(), f"output_{uuid.uuid4().hex}.json")

    def tearDown(self):
        if os.path.exists(self.output_path):
            try:
                os.remove(self.output_path)
            except OSError:
                pass

    def test_realtime_anomaly_reactor_init(self):
        self.assertEqual(self.reactor.stream_source, self.stream_source_val)
        self.assertIsNotNone(self.reactor.ingestor)
        self.assertIsNotNone(self.reactor.detector)

    def test_process_stream_payload_with_analyze_stream(self):
        ingest_res = {"status": "ok", "id": uuid.uuid4().hex}
        analysis_res = {"anomaly": False, "score": random.random()}

        with patch("skills.market_portfolio_realtime_anomaly_reactor_v2.market_portfolio_realtime_stream_ingestor", return_value=ingest_res) as mock_ing:
            with patch.object(self.reactor.detector, "analyze_stream", return_value=analysis_res, create=True) as mock_det:
                if hasattr(self.reactor.detector, "detect"):
                    delattr(self.reactor.detector, "detect")
                
                result = self.reactor.process_stream_payload(self.payload, self.output_path)

                mock_ing.assert_called_once_with(self.payload, self.output_path)
                mock_det.assert_called_once_with(self.payload)
                self.assertEqual(result["ingestion"], ingest_res)
                self.assertEqual(result["anomaly_analysis"], analysis_res)
                self.assertTrue(result["reactor_status"])

    def test_process_stream_payload_with_detect(self):
        ingest_res = {"status": "success", "uuid": uuid.uuid4().hex}
        analysis_res = {"anomaly": True, "level": random.randint(1, 5)}

        with patch("skills.market_portfolio_realtime_anomaly_reactor_v2.market_portfolio_realtime_stream_ingestor", return_value=ingest_res) as mock_ing:
            with patch.object(self.reactor.detector, "detect", return_value=analysis_res, create=True) as mock_det:
                if hasattr(self.reactor.detector, "analyze_stream"):
                    delattr(self.reactor.detector, "analyze_stream")

                result = self.reactor.process_stream_payload(self.payload, self.output_path)

                mock_ing.assert_called_once_with(self.payload, self.output_path)
                mock_det.assert_called_once_with(self.payload)
                self.assertEqual(result["ingestion"], ingest_res)
                self.assertEqual(result["anomaly_analysis"], analysis_res)
                self.assertTrue(result["reactor_status"])

    def test_start_live_monitoring(self):
        stream_id = uuid.uuid4().hex
        state_val = f"state_{uuid.uuid4().hex[:6]}"
        metrics_val = {"latency_ms": random.randint(1, 100)}
        stream_data = {
            "stream_id": stream_id,
            "state": state_val,
            "metrics": metrics_val
        }
        analysis_res = {"risk_score": random.uniform(0.0, 1.0)}

        with patch("skills.market_portfolio_realtime_anomaly_reactor_v2.start_new", return_value=stream_data) as mock_start:
            with patch.object(self.reactor.detector, "detect", return_value=analysis_res, create=True) as mock_det:
                context = {"env": uuid.uuid4().hex}
                res = self.reactor.start_live_monitoring(context)

                mock_start.assert_called_once_with(context, self.stream_source_val)
                mock_det.assert_called_once_with(stream_data)
                self.assertEqual(res["stream_id"], stream_id)
                self.assertEqual(res["state"], state_val)
                self.assertEqual(res["metrics"], metrics_val)
                self.assertEqual(res["analysis"], analysis_res)

    def test_reactor_entry_point_integration(self):
        ingest_res = {"code": 200, "uuid": uuid.uuid4().hex}
        det_res = {"anomaly_detected": False, "confidence": random.random()}

        with patch("skills.market_portfolio_realtime_anomaly_reactor_v2.market_portfolio_realtime_stream_ingestor", return_value=ingest_res) as mock_ing:
            with patch("skills.market_anomaly_detector.MarketAnomalyDetector.detect", return_value=det_res, create=True) as mock_det:
                res = reactor_entry_point(self.payload, self.output_path)

                mock_ing.assert_called_once_with(self.payload, self.output_path)
                mock_det.assert_called_once_with(self.payload)
                self.assertTrue(res["processed"])
                self.assertEqual(res["ingestion"], ingest_res)
                self.assertEqual(res["detection"], det_res)

    def test_market_portfolio_realtime_anomaly_reactor_v2_full(self):
        ingest_res = {"stored": True, "transaction_id": uuid.uuid4().hex}
        det_res = {"status": "normal", "timestamp": random.randint(100000, 999999)}
        ticker_val = self.payload["ticker"]

        with patch("skills.market_portfolio_realtime_anomaly_reactor_v2.market_portfolio_realtime_stream_ingestor", return_value=ingest_res) as mock_ing:
            with patch("skills.market_anomaly_detector.MarketAnomalyDetector.detect", return_value=det_res, create=True) as mock_det:
                res = market_portfolio_realtime_anomaly_reactor_v2(self.payload, self.output_path)

                mock_ing.assert_called_once_with(self.payload, self.output_path)
                mock_det.assert_called_once_with(self.payload)
                self.assertEqual(res["status"], "success")
                self.assertEqual(res["ticker"], ticker_val)
                self.assertEqual(res["ingestion"], ingest_res)
                self.assertEqual(res["detection"], det_res)

                self.assertTrue(os.path.exists(self.output_path))
                with open(self.output_path, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                self.assertEqual(file_data["status"], "success")
                self.assertEqual(file_data["ticker"], ticker_val)
                self.assertEqual(file_data["ingestion"], ingest_res)
                self.assertEqual(file_data["detection"], det_res)


if __name__ == "__main__":
    unittest.main()