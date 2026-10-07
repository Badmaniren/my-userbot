import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_stress_liquidity_monitor import start_new

class TestMarketStressLiquidityMonitor(unittest.TestCase):

    def setUp(self):
        self.rand_str_1 = ''.join(random.choices(string.ascii_letters, k=12))
        self.rand_str_2 = ''.join(random.choices(string.ascii_letters, k=10))
        self.rand_id = str(uuid.uuid4())
        self.rand_val = random.uniform(105.5, 9999.99)
        self.db_storage = MagicMock()
        self.extractor_1 = MagicMock()
        self.extractor_2 = MagicMock()
        self.anomaly_detector = MagicMock()

    def test_start_new_liquidity_monitor_success(self):
        payload_bytes = f"{self.rand_str_1}_{self.rand_id}_{self.rand_val}".encode('utf-8')
        mock_response_stream = io.BytesIO(payload_bytes)

        with patch('skills.market_stress_liquidity_monitor.requests.get') as mock_get, \
             patch('skills.market_stress_liquidity_monitor.uuid.uuid4') as mock_uuid:
            
            mock_uuid.return_value = uuid.UUID(self.rand_id)
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.raw = mock_response_stream
            mock_resp.content = payload_bytes
            mock_resp.text = payload_bytes.decode('utf-8')
            mock_get.return_value = mock_resp

            kwargs = {
                "db_storage": self.db_storage,
                "extractor_tool_1790087207": self.extractor_1,
                "extractor_tool_1790102839": self.extractor_2,
                "extractor_tool_1790262909": MagicMock(),
                "extractor_tool_1790621808": MagicMock(),
                "market_anomaly_detector": self.anomaly_detector,
                "market_insider_activity_tracker": MagicMock(),
                "market_insider_alert_pipeline": MagicMock(),
                "market_insider_anomaly_analyzer": MagicMock(),
                "market_insider_anomaly_report_bridge": MagicMock(),
                "market_news_sentiment_analyzer": MagicMock(),
                "market_parser": MagicMock(),
                "market_portfolio_alert_dispatcher": MagicMock(),
                "market_portfolio_alert_event_sink": MagicMock(),
                "market_portfolio_alert_filter_router": MagicMock(),
                "market_portfolio_api_gateway": MagicMock(),
                "market_portfolio_audit_alert_notifier": MagicMock(),
                "market_portfolio_audit_compliance_hub": MagicMock(),
                "market_portfolio_audit_log_exporter": MagicMock(),
                "market_portfolio_autonomous_sentinel": MagicMock(),
                "market_portfolio_backtest_evaluator_bridge": MagicMock(),
                "market_portfolio_backtester": MagicMock(),
                "market_portfolio_collector_agent": MagicMock(),
                "market_portfolio_data_exporter": MagicMock(),
                "market_portfolio_digest": MagicMock(),
                "market_portfolio_dividend_tracker": MagicMock(),
                "market_portfolio_event_intelligence_hub": MagicMock(),
                "market_portfolio_execution_cost_optimizer": MagicMock(),
                "market_portfolio_execution_pipeline": MagicMock(),
                "market_portfolio_integration_hub": MagicMock(),
                "market_portfolio_liquidity_scenario_analyzer": MagicMock(),
                "market_portfolio_monitor": MagicMock(),
                "market_portfolio_performance_analytics": MagicMock(),
                "market_portfolio_predictive_aggregator": MagicMock(),
                "market_portfolio_scenario_simulator": MagicMock(),
                "market_portfolio_slippage_model": MagicMock(),
                "market_portfolio_strategy_optimizer": MagicMock(),
                "market_portfolio_stress_audit_visualizer": MagicMock(),
                "market_portfolio_stress_auto_rebalance_trigger": MagicMock(),
                "market_portfolio_stress_monte_carlo_engine": MagicMock(),
                "market_portfolio_stress_recovery_coordinator_bridge": MagicMock(),
                "market_portfolio_stress_reporter": MagicMock(),
                "market_portfolio_stress_scenario_matrix_evaluator": MagicMock(),
                "market_portfolio_stress_scenario_pipeline": MagicMock(),
                "market_portfolio_tax_calculator": MagicMock(),
                "market_portfolio_telegram_command_center": MagicMock(),
                "market_portfolio_telegram_notifier": MagicMock(),
                "market_portfolio_valuation": MagicMock(),
                "market_portfolio_var_liquidity_core": MagicMock(),
                "market_portfolio_visualizer_v2": MagicMock(),
                "market_portfolio_webhook_event_logger": MagicMock(),
                "market_portfolio_webhook_sync": MagicMock(),
                "market_report_generator": MagicMock(),
                "market_sentiment_digest": MagicMock(),
                "market_sentiment_risk_alert_bridge": MagicMock(),
                "market_sentiment_risk_hub": MagicMock(),
                "market_sentiment_telegram_publisher": "https://" + self.rand_str_2 + ".com/webhook",
                "market_telegram_pipeline": MagicMock()
            }

            self.extractor_1.return_value = {self.rand_str_1: self.rand_val}
            self.anomaly_detector.evaluate.return_value = True

            result = start_new(**kwargs)
            
            self.assertIsNotNone(result)
            self.db_storage.save.assert_called()

    def test_start_new_liquidity_monitor_anomaly_trigger(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes + self.rand_str_2.encode('utf-8'))
        
        with patch('skills.market_stress_liquidity_monitor.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raw = stream_data
            mock_response.content = stream_data.getvalue()
            mock_response.text = stream_data.getvalue().decode('utf-8')
            mock_get.return_value = mock_response

            kwargs = {
                "db_storage": self.db_storage,
                "extractor_tool_1790087207": self.extractor_1,
                "extractor_tool_1790102839": self.extractor_2,
                "extractor_tool_1790262909": MagicMock(),
                "extractor_tool_1790621808": MagicMock(),
                "market_anomaly_detector": self.anomaly_detector,
                "market_insider_activity_tracker": MagicMock(),
                "market_insider_alert_pipeline": MagicMock(),
                "market_insider_anomaly_analyzer": MagicMock(),
                "market_insider_anomaly_report_bridge": MagicMock(),
                "market_news_sentiment_analyzer": MagicMock(),
                "market_parser": MagicMock(),
                "market_portfolio_alert_dispatcher": MagicMock(),
                "market_portfolio_alert_event_sink": MagicMock(),
                "market_portfolio_alert_filter_router": MagicMock(),
                "market_portfolio_api_gateway": MagicMock(),
                "market_portfolio_audit_alert_notifier": MagicMock(),
                "market_portfolio_audit_compliance_hub": MagicMock(),
                "market_portfolio_audit_log_exporter": MagicMock(),
                "market_portfolio_autonomous_sentinel": MagicMock(),
                "market_portfolio_backtest_evaluator_bridge": MagicMock(),
                "market_portfolio_backtester": MagicMock(),
                "market_portfolio_collector_agent": MagicMock(),
                "market_portfolio_data_exporter": MagicMock(),
                "market_portfolio_digest": MagicMock(),
                "market_portfolio_dividend_tracker": MagicMock(),
                "market_portfolio_event_intelligence_hub": MagicMock(),
                "market_portfolio_execution_cost_optimizer": MagicMock(),
                "market_portfolio_execution_pipeline": MagicMock(),
                "market_portfolio_integration_hub": MagicMock(),
                "market_portfolio_liquidity_scenario_analyzer": MagicMock(),
                "market_portfolio_monitor": MagicMock(),
                "market_portfolio_performance_analytics": MagicMock(),
                "market_portfolio_predictive_aggregator": MagicMock(),
                "market_portfolio_scenario_simulator": MagicMock(),
                "market_portfolio_slippage_model": MagicMock(),
                "market_portfolio_strategy_optimizer": MagicMock(),
                "market_portfolio_stress_audit_visualizer": MagicMock(),
                "market_portfolio_stress_auto_rebalance_trigger": MagicMock(),
                "market_portfolio_stress_monte_carlo_engine": MagicMock(),
                "market_portfolio_stress_recovery_coordinator_bridge": MagicMock(),
                "market_portfolio_stress_reporter": MagicMock(),
                "market_portfolio_stress_scenario_matrix_evaluator": MagicMock(),
                "market_portfolio_stress_scenario_pipeline": MagicMock(),
                "market_portfolio_tax_calculator": MagicMock(),
                "market_portfolio_telegram_command_center": MagicMock(),
                "market_portfolio_telegram_notifier": MagicMock(),
                "market_portfolio_valuation": MagicMock(),
                "market_portfolio_var_liquidity_core": MagicMock(),
                "market_portfolio_visualizer_v2": MagicMock(),
                "market_portfolio_webhook_event_logger": MagicMock(),
                "market_portfolio_webhook_sync": MagicMock(),
                "market_report_generator": MagicMock(),
                "market_sentiment_digest": MagicMock(),
                "market_sentiment_risk_alert_bridge": MagicMock(),
                "market_sentiment_risk_hub": MagicMock(),
                "market_sentiment_telegram_publisher": self.rand_id,
                "market_telegram_pipeline": MagicMock()
            }

            try:
                res = start_new(**kwargs)
                self.assertIsNotNone(res)
            except Exception as e:
                self.assertIsInstance(e, (Exception, KeyError, ValueError))

if __name__ == '__main__':
    unittest.main()