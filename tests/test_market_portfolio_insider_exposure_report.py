import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.market_portfolio_insider_exposure_report import (
    MarketPortfolioInsiderExposureReporter,
    generate_insider_exposure_report
)


class TestMarketPortfolioInsiderExposureReport(unittest.TestCase):

    def setUp(self):
        self.rand_metric_key = uuid.uuid4().hex
        self.rand_metric_val = random.randint(1000, 99999)
        self.rand_alert_msg = f"ALERT_{uuid.uuid4().hex}"

    def test_build_report_with_real_db_mock(self):
        mock_db = MagicMock()
        mock_db.fetch_exposure_data.return_value = {
            self.rand_metric_key: self.rand_metric_val
        }

        payload = {'db_storage': mock_db}
        reporter = MarketPortfolioInsiderExposureReporter(payload_data=payload)
        report = reporter.build_report()

        self.assertIsInstance(report, dict)
        self.assertIn('report_id', report)
        self.assertEqual(report['exposure_metric'], self.rand_metric_val)
        self.assertEqual(report['status'], 'active')
        mock_db.fetch_exposure_data.assert_called_once()

    def test_build_report_empty_db(self):
        reporter = MarketPortfolioInsiderExposureReporter(payload_data={})
        report = reporter.build_report()

        self.assertEqual(report['exposure_metric'], 0)
        self.assertEqual(report['status'], 'active')

    def test_process_exposure_streams_invokes_tools(self):
        mock_extractor = MagicMock()
        mock_monitor = MagicMock()

        payload = {
            'extractor_tool_1790087207': mock_extractor,
            'market_portfolio_monitor': mock_monitor
        }
        reporter = MarketPortfolioInsiderExposureReporter(payload_data=payload)
        tokens = reporter.process_exposure_streams()

        self.assertIsInstance(tokens, list)
        self.assertTrue(len(tokens) > 0)
        mock_extractor.extract_stream.assert_called_once()
        mock_monitor.evaluate_risk.assert_called_once()

    def test_compile_anomaly_section_success(self):
        rand_score = random.random() * 100
        mock_detector = MagicMock()
        mock_detector.detect_exposure_spikes.return_value = {
            'anomaly_score': rand_score,
            'flagged': True
        }

        payload = {'market_anomaly_detector': mock_detector}
        reporter = MarketPortfolioInsiderExposureReporter(payload_data=payload)
        result = reporter.compile_anomaly_section()

        self.assertEqual(result['anomaly_score'], rand_score)
        self.assertTrue(result['flagged'])
        mock_detector.detect_exposure_spikes.assert_called_once()

    def test_compile_anomaly_section_default(self):
        reporter = MarketPortfolioInsiderExposureReporter(payload_data={})
        result = reporter.compile_anomaly_section()
        self.assertEqual(result['anomaly_score'], 0.0)
        self.assertFalse(result['flagged'])

    def test_trigger_alerts_dispatches_signal(self):
        mock_dispatcher = MagicMock()
        mock_dispatcher.dispatch_signal.return_value = True

        payload = {'market_portfolio_alert_dispatcher': mock_dispatcher}
        reporter = MarketPortfolioInsiderExposureReporter(payload_data=payload)
        res = reporter.trigger_alerts(self.rand_alert_msg)

        self.assertTrue(res)
        mock_dispatcher.dispatch_signal.assert_called_once_with(self.rand_alert_msg)

    def test_run_audit_check_compliance(self):
        rand_hash = uuid.uuid4().hex
        mock_hub = MagicMock()
        mock_hub.verify_compliance.return_value = {'compliant': True, 'hash': rand_hash}
        mock_exporter = MagicMock()

        payload = {
            'market_portfolio_audit_compliance_hub': mock_hub,
            'market_portfolio_audit_log_exporter': mock_exporter
        }
        reporter = MarketPortfolioInsiderExposureReporter(payload_data=payload)
        res = reporter.run_audit_check()

        self.assertTrue(res['compliant'])
        self.assertEqual(res['hash'], rand_hash)
        mock_hub.verify_compliance.assert_called_once()
        mock_exporter.export.assert_called_once()

    def test_generate_insider_exposure_report_functional(self):
        mock_db = MagicMock()
        mock_db.fetch_exposure_data.return_value = {
            uuid.uuid4().hex: random.randint(1, 500)
        }
        payload = {'db_storage': mock_db}

        report = generate_insider_exposure_report(payload)
        self.assertIn('report_id', report)
        self.assertIn('exposure_metric', report)


if __name__ == '__main__':
    unittest.main()