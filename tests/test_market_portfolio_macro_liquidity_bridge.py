import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import os

from skills.market_portfolio_macro_liquidity_bridge import MarketPortfolioMacroLiquidityBridge

class TestMarketPortfolioMacroLiquidityBridge(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.threshold = random.uniform(0.1, 99.9)
        self.chat_id = str(random.randint(100000, 999999))
        self.message = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        self.export_path = f"test_export_{uuid.uuid4().hex}.log"
        self.stream_data = ''.join(random.choices(string.ascii_letters, k=32)).encode('utf-8')

        self.mock_db_storage = MagicMock()
        self.mock_var_liquidity_core = MagicMock()
        self.mock_market_parser = MagicMock()
        self.mock_anomaly_detector = MagicMock()
        self.mock_alert_dispatcher = MagicMock()
        self.mock_audit_exporter = MagicMock()
        self.mock_telegram_pipeline = MagicMock()

        self.bridge = MarketPortfolioMacroLiquidityBridge(
            db_storage=self.mock_db_storage,
            market_portfolio_var_liquidity_core=self.mock_var_liquidity_core,
            market_parser=self.mock_market_parser,
            market_anomaly_detector=self.mock_anomaly_detector,
            market_portfolio_alert_dispatcher=self.mock_alert_dispatcher,
            market_portfolio_audit_log_exporter=self.mock_audit_exporter,
            market_telegram_pipeline=self.mock_telegram_pipeline
        )

    def tearDown(self):
        if os.path.exists(self.export_path):
            try:
                os.remove(self.export_path)
            except OSError:
                pass

    def test_synchronize_macro_liquidity(self):
        db_fetch_result = {"data": uuid.uuid4().hex}
        self.mock_db_storage.fetch.return_value = db_fetch_result

        expected_liquidity_score = random.uniform(1.0, 100.0)
        self.mock_var_liquidity_core.calculate.return_value = expected_liquidity_score

        expected_macro_factor = random.uniform(0.5, 5.0)
        mock_response = MagicMock()
        mock_response.json.return_value = {"macro_factor": expected_macro_factor}

        with patch('requests.get', return_value=mock_response) as mock_get:
            result = self.bridge.synchronize_macro_liquidity(self.portfolio_id)

            self.mock_db_storage.fetch.assert_called_once_with(self.portfolio_id)
            self.mock_var_liquidity_core.calculate.assert_called_once_with(self.portfolio_id, db_fetch_result)
            mock_get.assert_called_once_with("https://example.com/api/macro")

            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["liquidity_score"], expected_liquidity_score)
            self.assertEqual(result["macro_value"], expected_macro_factor)

    def test_process_macro_stream(self):
        stream = io.BytesIO(self.stream_data)
        expected_parsed_output = {"status": uuid.uuid4().hex}
        self.mock_market_parser.parse_stream.return_value = expected_parsed_output

        result = self.bridge.process_macro_stream(stream)

        self.mock_market_parser.parse_stream.assert_called_once_with(stream)
        self.assertEqual(result, expected_parsed_output)

    def test_evaluate_and_dispatch_anomalies(self):
        anomaly_id = uuid.uuid4().hex
        anomaly_data = {"anomaly_id": anomaly_id, "metric": random.random()}
        self.mock_anomaly_detector.detect.return_value = anomaly_data

        dispatched_status = random.choice([True, False])
        self.mock_alert_dispatcher.dispatch.return_value = dispatched_status

        result = self.bridge.evaluate_and_dispatch_anomalies(self.threshold)

        self.mock_anomaly_detector.detect.assert_called_once_with(self.threshold)
        self.mock_alert_dispatcher.dispatch.assert_called_once_with(anomaly_data)

        self.assertEqual(result["anomaly_id"], anomaly_id)
        self.assertEqual(result["dispatched"], dispatched_status)

    def test_export_audit_logs_bridge(self):
        audit_logs = [{"log_id": uuid.uuid4().hex, "timestamp": random.randint(1000, 9999)}]
        self.mock_db_storage.get_audit_logs.return_value = audit_logs

        exported_path = f"/var/log/{uuid.uuid4().hex}.log"
        self.mock_audit_exporter.export.return_value = exported_path

        result = self.bridge.export_audit_logs_bridge(self.export_path)

        self.mock_db_storage.get_audit_logs.assert_called_once()
        self.mock_audit_exporter.export.assert_called_once_with(audit_logs)
        self.assertEqual(result, exported_path)

        self.assertTrue(os.path.exists(self.export_path))
        with open(self.export_path, "r") as f:
            content = f.read()
        self.assertIn(str(audit_logs), content)

    def test_send_telegram_alert(self):
        expected_response = {"ok": True, "message_id": random.randint(1, 10000)}
        self.mock_telegram_pipeline.send_message.return_value = expected_response

        result = self.bridge.send_telegram_alert(self.chat_id, self.message)

        self.mock_telegram_pipeline.send_message.assert_called_once_with(self.chat_id, self.message)
        self.assertEqual(result, expected_response)

if __name__ == '__main__':
    unittest.main()