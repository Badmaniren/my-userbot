import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import sys
import os

from skills.market_anomaly_detector import (
    MarketAnomalyDetector,
    market_anomaly_detector,
    detect_anomalies,
    dispatch_anomaly_alert,
    export_anomaly_audit
)


class TestMarketAnomalyDetector(unittest.TestCase):

    def setUp(self):
        self.ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        self.threshold = random.randint(1000, 50000)
        self.anomaly_id = uuid.uuid4().hex
        self.log_msg = f"LOG_{uuid.uuid4().hex}"

    def test_market_anomaly_detector_factory_and_class(self):
        db_mock = MagicMock()
        parser_mock = MagicMock()
        tracker_mock = MagicMock()
        monitor_mock = MagicMock()
        alert_mock = MagicMock()

        detector = market_anomaly_detector(
            storage=db_mock,
            parser=parser_mock,
            insider_tracker=tracker_mock,
            monitor=monitor_mock,
            alert_dispatcher=alert_mock
        )

        self.assertIsInstance(detector, MarketAnomalyDetector)
        self.assertEqual(detector.db_storage, db_mock)
        self.assertEqual(detector.market_parser, parser_mock)
        self.assertEqual(detector.market_insider_activity_tracker, tracker_mock)
        self.assertEqual(detector.monitor, monitor_mock)
        self.assertEqual(detector.alert_dispatcher, alert_mock)

    def test_analyze_ticker_with_save_anomaly(self):
        db_mock = MagicMock()
        del db_mock.store_anomaly
        detector = MarketAnomalyDetector(db_storage=db_mock)

        result = detector.analyze_ticker(self.ticker, self.threshold)

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("anomaly_detected"))
        self.assertEqual(result.get("ticker"), self.ticker)
        db_mock.save_anomaly.assert_called_once_with({"ticker": self.ticker})

    def test_analyze_ticker_with_store_anomaly(self):
        db_mock = MagicMock()
        del db_mock.save_anomaly
        detector = MarketAnomalyDetector(db_storage=db_mock)

        result = detector.analyze_ticker(self.ticker, self.threshold)

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("anomaly_detected"))
        self.assertEqual(result.get("ticker"), self.ticker)
        db_mock.store_anomaly.assert_called_once_with({"ticker": self.ticker})

    def test_detect_anomalies_with_gateway(self):
        gateway_mock = MagicMock()
        expected_data = {"market_data_id": uuid.uuid4().hex, "volume": random.randint(100, 9999)}
        gateway_mock.fetch_market_data.return_value = expected_data

        res = detect_anomalies(self.anomaly_id, gateway=gateway_mock)

        self.assertEqual(res, expected_data)
        gateway_mock.fetch_market_data.assert_called_once()

    def test_detect_anomalies_without_gateway(self):
        res = detect_anomalies(self.anomaly_id, gateway=None)

        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("anomaly_id"), self.anomaly_id)

    def test_dispatch_anomaly_alert_with_dispatcher(self):
        payload = {"alert_uuid": uuid.uuid4().hex, "metric": random.random()}
        mock_dispatcher = MagicMock()

        import skills.market_anomaly_detector as mad_module
        old_disp = getattr(mad_module, 'market_portfolio_alert_dispatcher', None)
        mad_module.market_portfolio_alert_dispatcher = mock_dispatcher
        try:
            dispatch_anomaly_alert(payload)
            mock_dispatcher.send.assert_called_once_with(payload)
        finally:
            if old_disp is not None:
                mad_module.market_portfolio_alert_dispatcher = old_disp
            else:
                if hasattr(mad_module, 'market_portfolio_alert_dispatcher'):
                    delattr(mad_module, 'market_portfolio_alert_dispatcher')

    def test_export_anomaly_audit_with_exporter(self):
        mock_exporter = MagicMock()

        import skills.market_anomaly_detector as mad_module
        old_exp = getattr(mad_module, 'market_portfolio_audit_log_exporter', None)
        mad_module.market_portfolio_audit_log_exporter = mock_exporter
        try:
            export_anomaly_audit(self.log_msg)
            mock_exporter.write_log.assert_called_once_with(self.log_msg)
        finally:
            if old_exp is not None:
                mad_module.market_portfolio_audit_log_exporter = old_exp
            else:
                if hasattr(mad_module, 'market_portfolio_audit_log_exporter'):
                    delattr(mad_module, 'market_portfolio_audit_log_exporter')


if __name__ == '__main__':
    unittest.main()