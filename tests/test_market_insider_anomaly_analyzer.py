import io
import random
import string
import sys
import unittest
from unittest.mock import MagicMock, patch
import uuid

import skills.market_insider_anomaly_analyzer as analyzer_module


class TestMarketInsiderAnomalyAnalyzer(unittest.TestCase):
    def setUp(self):
        self.random_ticker = f"TCK_{uuid.uuid4().hex[:6].upper()}"
        self.random_exchange = f"EXCH_{uuid.uuid4().hex[:8].upper()}"
        self.random_id = uuid.uuid4().hex
        self.random_score = round(random.uniform(0.75, 0.99), 4)
        self.random_volume = random.randint(10000, 5000000)

    def _get_analyzer_instance(self, detector_mock=None, pipeline_mock=None):
        if hasattr(analyzer_module, "MarketInsiderAnomalyAnalyzer"):
            cls = getattr(analyzer_module, "MarketInsiderAnomalyAnalyzer")
            try:
                if detector_mock is not None or pipeline_mock is not None:
                    return cls(anomaly_detector=detector_mock, alert_pipeline=pipeline_mock)
                return cls()
            except TypeError:
                return cls()
        return None

    def _invoke_ticker_analysis(self, instance, ticker, stream_data=None):
        if instance is not None:
            for method_name in ["analyze_ticker", "analyze", "detect", "correlate", "process"]:
                if hasattr(instance, method_name):
                    method = getattr(instance, method_name)
                    try:
                        return method(ticker, stream_data)
                    except TypeError:
                        return method(ticker)
        if hasattr(analyzer_module, "market_insider_anomaly_analyzer"):
            func = getattr(analyzer_module, "market_insider_anomaly_analyzer")
            try:
                return func(ticker=ticker, raw_stream_data=stream_data)
            except TypeError:
                return func({"ticker": ticker, "raw_stream_data": stream_data})
        raise AttributeError("No ticker analysis method or function found in market_insider_anomaly_analyzer")

    def _invoke_stream_analysis(self, instance, exchange):
        if instance is not None:
            for method_name in [
                "analyze_stream",
                "evaluate_exchange",
                "analyze_exchange",
                "evaluate_market_stream",
                "correlate_exchange",
            ]:
                if hasattr(instance, method_name):
                    return getattr(instance, method_name)(exchange)
        if hasattr(analyzer_module, "evaluate_exchange_anomalies"):
            return getattr(analyzer_module, "evaluate_exchange_anomalies")(exchange)
        raise AttributeError("No stream analysis method found in market_insider_anomaly_analyzer")

    def test_imports_and_components_exist(self):
        has_class = hasattr(analyzer_module, "MarketInsiderAnomalyAnalyzer")
        has_func = hasattr(analyzer_module, "market_insider_anomaly_analyzer")
        self.assertTrue(
            has_class or has_func,
            "Module must provide MarketInsiderAnomalyAnalyzer class or market_insider_anomaly_analyzer function",
        )

    def test_coordinated_suspicious_activity_detected(self):
        anomaly_id = f"ANOM_{uuid.uuid4().hex}"
        alert_id = f"ALERT_{uuid.uuid4().hex}"
        anomaly_metric = round(random.uniform(0.8, 0.99), 3)

        mock_detector_result = {
            "ticker": self.random_ticker,
            "has_anomaly": True,
            "anomaly_id": anomaly_id,
            "score": anomaly_metric,
        }
        mock_pipeline_result = {
            "ticker": self.random_ticker,
            "insider_detected": True,
            "alerts": [{"alert_id": alert_id, "confidence": anomaly_metric, "volume": self.random_volume}],
        }

        with patch("skills.market_insider_anomaly_analyzer.MarketAnomalyDetector") as mock_det_cls, \
             patch("skills.market_insider_anomaly_analyzer.MarketInsiderAlertPipeline") as mock_pipe_cls:

            det_instance = mock_det_cls.return_value
            det_instance.detect.return_value = mock_detector_result

            pipe_instance = mock_pipe_cls.return_value
            pipe_instance.process_alert_stream.return_value = mock_pipeline_result

            analyzer = self._get_analyzer_instance(detector_mock=det_instance, pipeline_mock=pipe_instance)
            raw_payload = io.BytesIO(f"raw_stream_{uuid.uuid4().hex}".encode("utf-8"))

            result = self._invoke_ticker_analysis(analyzer, self.random_ticker, raw_payload)

            self.assertIsNotNone(result)
            serialized_result = str(result)
            self.assertIn(
                self.random_ticker,
                serialized_result,
                f"Expected ticker {self.random_ticker} in correlated output",
            )

            is_coordinated = (
                result.get("is_coordinated")
                or result.get("suspicious")
                or result.get("coordinated_activity")
                or result.get("flagged")
                or (result.get("status") in ["coordinated", "suspicious", "high_risk", "ALERT"])
            )
            self.assertTrue(
                is_coordinated,
                "Both anomaly and insider alert present; activity must be flagged as coordinated/suspicious",
            )

            if isinstance(result, dict) and "anomaly_id" in serialized_result:
                self.assertIn(anomaly_id, serialized_result)
            if isinstance(result, dict) and "alert_id" in serialized_result:
                self.assertIn(alert_id, serialized_result)

    def test_benign_activity_when_no_anomalies_or_alerts(self):
        clean_ticker = f"CLN_{uuid.uuid4().hex[:6].upper()}"

        mock_detector_result = {
            "ticker": clean_ticker,
            "has_anomaly": False,
            "score": round(random.uniform(0.01, 0.1), 3),
        }
        mock_pipeline_result = {
            "ticker": clean_ticker,
            "insider_detected": False,
            "alerts": [],
        }

        with patch("skills.market_insider_anomaly_analyzer.MarketAnomalyDetector") as mock_det_cls, \
             patch("skills.market_insider_anomaly_analyzer.MarketInsiderAlertPipeline") as mock_pipe_cls:

            det_instance = mock_det_cls.return_value
            det_instance.detect.return_value = mock_detector_result

            pipe_instance = mock_pipe_cls.return_value
            pipe_instance.process_alert_stream.return_value = mock_pipeline_result

            analyzer = self._get_analyzer_instance(detector_mock=det_instance, pipeline_mock=pipe_instance)
            result = self._invoke_ticker_analysis(analyzer, clean_ticker, None)

            self.assertIsNotNone(result)
            is_coordinated = (
                result.get("is_coordinated")
                or result.get("suspicious")
                or result.get("coordinated_activity")
                or False
            )
            self.assertFalse(is_coordinated, "Normal trading activity must not be flagged as coordinated")

    def test_exchange_stream_correlation_aggregation(self):
        stream_token = f"STREAM_{uuid.uuid4().hex}"
        anomaly_items = [
            {"ticker": f"TCK_{uuid.uuid4().hex[:4].upper()}", "score": round(random.uniform(0.7, 0.95), 2)}
            for _ in range(3)
        ]
        insider_items = {
            "exchange": self.random_exchange,
            "token": stream_token,
            "events_count": random.randint(5, 50),
        }

        with patch("skills.market_insider_anomaly_analyzer.MarketAnomalyDetector") as mock_det_cls, \
             patch("skills.market_insider_anomaly_analyzer.MarketInsiderAlertPipeline") as mock_pipe_cls:

            det_instance = mock_det_cls.return_value
            det_instance.analyze_stream.return_value = anomaly_items

            pipe_instance = mock_pipe_cls.return_value
            pipe_instance.evaluate_market_stream.return_value = insider_items

            analyzer = self._get_analyzer_instance(detector_mock=det_instance, pipeline_mock=pipe_instance)
            result = self._invoke_stream_analysis(analyzer, self.random_exchange)

            self.assertIsNotNone(result)
            res_str = str(result)
            self.assertIn(self.random_exchange, res_str)
            det_instance.analyze_stream.assert_called_with(self.random_exchange)
            pipe_instance.evaluate_market_stream.assert_called_with(self.random_exchange)

    def test_dependency_injection_custom_instances(self):
        custom_detector = MagicMock()
        custom_pipeline = MagicMock()
        ret_val_det = {"score": self.random_score, "has_anomaly": False}
        ret_val_pipe = {"alerts": [], "insider_detected": False}

        custom_detector.detect.return_value = ret_val_det
        custom_pipeline.process_alert_stream.return_value = ret_val_pipe

        analyzer = self._get_analyzer_instance(
            detector_mock=custom_detector,
            pipeline_mock=custom_pipeline,
        )

        test_ticker = f"DI_{uuid.uuid4().hex[:5].upper()}"
        raw_io = io.BytesIO(f"payload_{uuid.uuid4().hex}".encode("latin1"))

        _ = self._invoke_ticker_analysis(analyzer, test_ticker, raw_io)

        custom_detector.detect.assert_called()
        self.assertTrue(
            custom_pipeline.process_alert_stream.called or custom_pipeline.evaluate_market_stream.called
        )


if __name__ == "__main__":
    unittest.main()