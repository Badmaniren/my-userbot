import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_stress_alert_dashboard_bridge import (
    StressAlertDashboardBridge,
    process_stress_dashboard_bridge
)


class TestMarketPortfolioStressAlertDashboardBridge(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.url = f"https://{uuid.uuid4().hex}.com/api"
        self.telegram_token = f"token_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))
        self.min_threshold = round(random.uniform(1.0, 10.0), 2)
        self.severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.shifts = [round(random.uniform(-50.0, 50.0), 2) for _ in range(3)]

    def test_bridge_initialization_and_composition(self):
        bridge = StressAlertDashboardBridge(self.storage_file)
        self.assertEqual(bridge.storage_file, self.storage_file)
        self.assertIsNotNone(bridge.emitter)
        self.assertIsNotNone(bridge.report_generator)

    @patch('skills.market_portfolio_stress_alert_dashboard_bridge.MarketReportGenerator')
    @patch('skills.market_portfolio_stress_alert_dashboard_bridge.StressAlertEmitter')
    def test_evaluate_and_generate_dashboard_success(self, mock_emitter_cls, mock_reporter_cls):
        mock_emitter_instance = mock_emitter_cls.return_value
        mock_emitter_instance.evaluate_and_emit.return_value = True

        mock_reporter_instance = mock_reporter_cls.return_value
        expected_report_data = {
            "report_id": uuid.uuid4().hex,
            "symbol": self.symbol,
            "status": "GENERATED"
        }
        mock_reporter_instance.generate_symbol_report.return_value = expected_report_data

        bridge = StressAlertDashboardBridge(self.storage_file)
        result = bridge.evaluate_and_generate_dashboard(
            symbol=self.symbol,
            shifts=self.shifts,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            min_threshold=self.min_threshold,
            severity_level=self.severity_level
        )

        mock_emitter_instance.evaluate_and_emit.assert_called_once_with(
            symbol=self.symbol,
            shifts=self.shifts,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            min_threshold=self.min_threshold,
            severity_level=self.severity_level
        )
        mock_reporter_instance.generate_symbol_report.assert_called_once_with(self.symbol)
        
        self.assertTrue(result["alert_triggered"])
        self.assertEqual(result["report"], expected_report_data)

    @patch('skills.market_portfolio_stress_alert_dashboard_bridge.MarketReportGenerator')
    @patch('skills.market_portfolio_stress_alert_dashboard_bridge.StressAlertEmitter')
    def test_evaluate_and_generate_dashboard_no_alert(self, mock_emitter_cls, mock_reporter_cls):
        mock_emitter_instance = mock_emitter_cls.return_value
        mock_emitter_instance.evaluate_and_emit.return_value = False

        mock_reporter_instance = mock_reporter_cls.return_value

        bridge = StressAlertDashboardBridge(self.storage_file)
        result = bridge.evaluate_and_generate_dashboard(
            symbol=self.symbol,
            shifts=self.shifts,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            min_threshold=self.min_threshold,
            severity_level=self.severity_level
        )

        mock_emitter_instance.evaluate_and_emit.assert_called_once()
        mock_reporter_instance.generate_symbol_report.assert_not_called()
        
        self.assertFalse(result["alert_triggered"])
        self.assertIsNone(result["report"])

    @patch('skills.market_portfolio_stress_alert_dashboard_bridge.MarketReportGenerator')
    @patch('skills.market_portfolio_stress_alert_dashboard_bridge.StressAlertEmitter')
    def test_process_stream_integration(self, mock_emitter_cls, mock_reporter_cls):
        mock_emitter_instance = mock_emitter_cls.return_value
        stream_id = uuid.uuid4().hex
        random_bytes = uuid.uuid4().bytes
        mock_emitter_instance.process_stream.return_value = io.BytesIO(random_bytes)

        bridge = StressAlertDashboardBridge(self.storage_file)
        stream_data = bridge.process_stress_stream(stream_id)

        mock_emitter_instance.process_stream.assert_called_once_with(stream_id)
        self.assertEqual(stream_data.read(), random_bytes)

    @patch('skills.market_portfolio_stress_alert_dashboard_bridge.MarketReportGenerator')
    @patch('skills.market_portfolio_stress_alert_dashboard_bridge.StressAlertEmitter')
    def test_functional_helper_wrapper(self, mock_emitter_cls, mock_reporter_cls):
        mock_emitter_instance = mock_emitter_cls.return_value
        mock_emitter_instance.evaluate_and_emit.return_value = True

        mock_reporter_instance = mock_reporter_cls.return_value
        mock_report = {"metrics": uuid.uuid4().hex}
        mock_reporter_instance.generate_symbol_report.return_value = mock_report

        res = process_stress_dashboard_bridge(
            storage_file=self.storage_file,
            symbol=self.symbol,
            shifts=self.shifts,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            min_threshold=self.min_threshold,
            severity_level=self.severity_level
        )

        self.assertTrue(res["alert_triggered"])
        self.assertEqual(res["report"], mock_report)


if __name__ == '__main__':
    unittest.main()