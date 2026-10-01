import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_stress_audit_logger import start_new


class TestMarketPortfolioStressAuditLogger(unittest.TestCase):

    def setUp(self):
        self.random_hex = uuid.uuid4().hex
        self.random_audit_id = f"audit_{uuid.uuid4().hex[:8]}"
        self.random_portfolio_id = f"portfolio_{uuid.uuid4().hex[:8]}"
        self.random_scenario_name = f"scenario_{random.choice(string.ascii_lowercase)}_{uuid.uuid4().hex[:6]}"
        self.random_risk_param = round(random.uniform(0.01, 0.99), 4)
        self.random_log_message = ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=32))
        
        self.mock_db_storage = MagicMock()
        self.mock_extractor_1790087207 = MagicMock()
        self.mock_extractor_1790102839 = MagicMock()
        self.mock_extractor_1790262909 = MagicMock()
        self.mock_extractor_1790621808 = MagicMock()
        self.mock_anomaly_detector = MagicMock()
        self.mock_insider_tracker = MagicMock()
        self.mock_alert_pipeline = MagicMock()
        self.mock_anomaly_analyzer = MagicMock()
        self.mock_report_bridge = MagicMock()
        self.mock_sentiment_analyzer = MagicMock()
        self.mock_parser = MagicMock()
        self.mock_alert_dispatcher = MagicMock()
        self.mock_event_sink = MagicMock()
        self.mock_filter_router = MagicMock()
        self.mock_api_gateway = MagicMock()
        self.mock_audit_notifier = MagicMock()
        self.mock_compliance_hub = MagicMock()
        self.mock_log_exporter = MagicMock()
        self.mock_autonomous_sentinel = MagicMock()
        self.mock_backtest_bridge = MagicMock()
        self.mock_backtester = MagicMock()
        self.mock_collector_agent = MagicMock()
        self.mock_data_exporter = MagicMock()
        self.mock_digest = MagicMock()
        self.mock_dividend_tracker = MagicMock()
        self.mock_event_intelligence_hub = MagicMock()
        self.mock_execution_cost_optimizer = MagicMock()
        self.mock_execution_pipeline = MagicMock()
        self.mock_integration_hub = MagicMock()
        self.mock_monitor = MagicMock()
        self.mock_performance_analytics = MagicMock()
        self.mock_predictive_aggregator = MagicMock()
        self.mock_scenario_simulator = MagicMock()
        self.mock_slippage_model = MagicMock()
        self.mock_strategy_optimizer = MagicMock()
        self.mock_monte_carlo_engine = MagicMock()
        self.mock_recovery_coordinator_bridge = MagicMock()
        self.mock_stress_reporter = MagicMock()
        self.mock_stress_scenario_pipeline = MagicMock()
        self.mock_tax_calculator = MagicMock()
        self.mock_telegram_command_center = MagicMock()
        self.mock_telegram_notifier = MagicMock()
        self.mock_valuation = MagicMock()
        self.mock_var_liquidity_core = MagicMock()
        self.mock_visualizer_v2 = MagicMock()
        self.mock_webhook_event_logger = MagicMock()
        self.mock_webhook_sync = MagicMock()
        self.mock_report_generator = MagicMock()
        self.mock_sentiment_digest = MagicMock()
        self.mock_sentiment_risk_alert_bridge = MagicMock()
        self.mock_sentiment_risk_hub = MagicMock()
        self.mock_sentiment_telegram_publisher = MagicMock()
        self.mock_telegram_pipeline = MagicMock()

    def test_start_new_success_flow(self):
        payload = {
            "audit_id": self.random_audit_id,
            "portfolio_id": self.random_portfolio_id,
            "scenario": self.random_scenario_name,
            "risk_param": self.random_risk_param,
            "message": self.random_log_message
        }
        
        self.mock_db_storage.save_audit_log.return_value = True
        self.mock_scenario_simulator.run_simulation.return_value = {
            "status": "success",
            "sim_id": self.random_hex
        }

        with patch('skills.market_portfolio_stress_audit_logger.db_storage', self.mock_db_storage), \
             patch('skills.market_portfolio_stress_audit_logger.market_portfolio_scenario_simulator', self.mock_scenario_simulator):
            
            result = start_new(payload)
            
            self.assertIsNotNone(result)
            self.assertIn("status", result)
            self.assertEqual(result.get("audit_id"), self.random_audit_id)
            self.mock_db_storage.save_audit_log.assert_called_once()
            args, _ = self.mock_db_storage.save_audit_log.call_args
            self.assertEqual(args[0]["portfolio_id"], self.random_portfolio_id)

    def test_start_new_with_stream_io(self):
        stream_data = io.BytesIO(self.random_log_message.encode('utf-8'))
        
        with patch('skills.market_portfolio_stress_audit_logger.market_parser', self.mock_parser):
            self.mock_parser.parse_stream.return_value = {
                "parsed_data": self.random_hex,
                "content": stream_data.read().decode('utf-8')
            }
            
            result = start_new({"stream_source": "active_stream"})
            self.assertEqual(result.get("parsed_data"), self.random_hex)
            self.mock_parser.parse_stream.assert_called_once()

    def test_start_new_anomaly_detection_trigger(self):
        anomaly_payload = {
            "anomaly_id": self.random_hex,
            "threshold": self.random_risk_param,
            "portfolio": self.random_portfolio_id
        }

        self.mock_anomaly_detector.evaluate.return_value = {
            "is_anomaly": True,
            "score": self.random_risk_param
        }

        with patch('skills.market_portfolio_stress_audit_logger.market_anomaly_detector', self.mock_anomaly_detector), \
             patch('skills.market_portfolio_stress_audit_logger.market_portfolio_alert_dispatcher', self.mock_alert_dispatcher):
            
            result = start_new(anomaly_payload)
            
            self.assertTrue(self.mock_alert_dispatcher.dispatch.called)
            self.assertEqual(result.get("anomaly_id"), self.random_hex)

    def test_start_new_exception_handling(self):
        failing_payload = {
            "fail_token": self.random_hex
        }

        with patch('skills.market_portfolio_stress_audit_logger.market_portfolio_var_liquidity_core', self.mock_var_liquidity_core):
            self.mock_var_liquidity_core.calculate.side_effect = ValueError(self.random_log_message)
            
            with self.assertRaises(ValueError) as ctx:
                start_new(failing_payload)
            
            self.assertIn(self.random_log_message, str(ctx.exception))


if __name__ == '__main__':
    unittest.main()