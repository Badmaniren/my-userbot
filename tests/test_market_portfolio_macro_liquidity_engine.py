import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
import requests
from bs4 import BeautifulSoup

from skills.market_portfolio_macro_liquidity_engine import MarketPortfolioMacroLiquidityEngine


class TestMarketPortfolioMacroLiquidityEngine(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_tool_1 = MagicMock()
        self.extractor_tool_2 = MagicMock()
        self.extractor_tool_3 = MagicMock()
        self.extractor_tool_4 = MagicMock()
        self.market_anomaly_detector = MagicMock()
        self.market_insider_activity_tracker = MagicMock()
        self.market_insider_alert_pipeline = MagicMock()
        self.market_insider_anomaly_analyzer = MagicMock()
        self.market_insider_anomaly_report_bridge = MagicMock()
        self.market_news_sentiment_analyzer = MagicMock()
        self.market_parser = MagicMock()
        self.market_portfolio_alert_dispatcher = MagicMock()
        self.market_portfolio_alert_event_sink = MagicMock()
        self.market_portfolio_alert_filter_router = MagicMock()
        self.market_portfolio_api_gateway = MagicMock()
        self.market_portfolio_audit_alert_notifier = MagicMock()
        self.market_portfolio_audit_compliance_hub = MagicMock()
        self.market_portfolio_audit_log_exporter = MagicMock()
        self.market_portfolio_autonomous_sentinel = MagicMock()
        self.market_portfolio_backtest_evaluator_bridge = MagicMock()
        self.market_portfolio_backtester = MagicMock()
        self.market_portfolio_collector_agent = MagicMock()
        self.market_portfolio_data_exporter = MagicMock()
        self.market_portfolio_digest = MagicMock()
        self.market_portfolio_dividend_tracker = MagicMock()
        self.market_portfolio_event_intelligence_hub = MagicMock()
        self.market_portfolio_execution_cost_optimizer = MagicMock()
        self.market_portfolio_execution_pipeline = MagicMock()
        self.market_portfolio_integration_hub = MagicMock()
        self.market_portfolio_monitor = MagicMock()
        self.market_portfolio_performance_analytics = MagicMock()
        self.market_portfolio_predictive_aggregator = MagicMock()
        self.market_portfolio_scenario_simulator = MagicMock()
        self.market_portfolio_slippage_model = MagicMock()
        self.market_portfolio_strategy_optimizer = MagicMock()
        self.market_portfolio_stress_audit_visualizer = MagicMock()
        self.market_portfolio_stress_monte_carlo_engine = MagicMock()
        self.market_portfolio_stress_recovery_coordinator_bridge = MagicMock()
        self.market_portfolio_stress_reporter = MagicMock()
        self.market_portfolio_stress_scenario_pipeline = MagicMock()
        self.market_portfolio_tax_calculator = MagicMock()
        self.market_portfolio_telegram_command_center = MagicMock()
        self.market_portfolio_telegram_notifier = MagicMock()
        self.market_portfolio_valuation = MagicMock()
        self.market_portfolio_var_liquidity_core = MagicMock()
        self.market_portfolio_visualizer_v2 = MagicMock()
        self.market_portfolio_webhook_event_logger = MagicMock()
        self.market_portfolio_webhook_sync = MagicMock()
        self.market_report_generator = MagicMock()
        self.market_sentiment_digest = MagicMock()
        self.market_sentiment_risk_alert_bridge = MagicMock()
        self.market_sentiment_risk_hub = MagicMock()
        self.market_sentiment_telegram_publisher = MagicMock()
        self.market_telegram_pipeline = MagicMock()

        self.engine = MarketPortfolioMacroLiquidityEngine(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_tool_1,
            extractor_tool_1790102839=self.extractor_tool_2,
            extractor_tool_1790262909=self.extractor_tool_3,
            extractor_tool_1790621808=self.extractor_tool_4,
            market_anomaly_detector=self.market_anomaly_detector,
            market_insider_activity_tracker=self.market_insider_activity_tracker,
            market_insider_alert_pipeline=self.market_insider_alert_pipeline,
            market_insider_anomaly_analyzer=self.market_insider_anomaly_analyzer,
            market_insider_anomaly_report_bridge=self.market_insider_anomaly_report_bridge,
            market_news_sentiment_analyzer=self.market_news_sentiment_analyzer,
            market_parser=self.market_parser,
            market_portfolio_alert_dispatcher=self.market_portfolio_alert_dispatcher,
            market_portfolio_alert_event_sink=self.market_portfolio_alert_event_sink,
            market_portfolio_alert_filter_router=self.market_portfolio_alert_filter_router,
            market_portfolio_api_gateway=self.market_portfolio_api_gateway,
            market_portfolio_audit_alert_notifier=self.market_portfolio_audit_alert_notifier,
            market_portfolio_audit_compliance_hub=self.market_portfolio_audit_compliance_hub,
            market_portfolio_audit_log_exporter=self.market_portfolio_audit_log_exporter,
            market_portfolio_autonomous_sentinel=self.market_portfolio_autonomous_sentinel,
            market_portfolio_backtest_evaluator_bridge=self.market_portfolio_backtest_evaluator_bridge,
            market_portfolio_backtester=self.market_portfolio_backtester,
            market_portfolio_collector_agent=self.market_portfolio_collector_agent,
            market_portfolio_data_exporter=self.market_portfolio_data_exporter,
            market_portfolio_digest=self.market_portfolio_digest,
            market_portfolio_dividend_tracker=self.market_portfolio_dividend_tracker,
            market_portfolio_event_intelligence_hub=self.market_portfolio_event_intelligence_hub,
            market_portfolio_execution_cost_optimizer=self.market_portfolio_execution_cost_optimizer,
            market_portfolio_execution_pipeline=self.market_portfolio_execution_pipeline,
            market_portfolio_integration_hub=self.market_portfolio_integration_hub,
            market_portfolio_monitor=self.market_portfolio_monitor,
            market_portfolio_performance_analytics=self.market_portfolio_performance_analytics,
            market_portfolio_predictive_aggregator=self.market_portfolio_predictive_aggregator,
            market_portfolio_scenario_simulator=self.market_portfolio_scenario_simulator,
            market_portfolio_slippage_model=self.market_portfolio_slippage_model,
            market_portfolio_strategy_optimizer=self.market_portfolio_strategy_optimizer,
            market_portfolio_stress_audit_visualizer=self.market_portfolio_stress_audit_visualizer,
            market_portfolio_stress_monte_carlo_engine=self.market_portfolio_stress_monte_carlo_engine,
            market_portfolio_stress_recovery_coordinator_bridge=self.market_portfolio_stress_recovery_coordinator_bridge,
            market_portfolio_stress_reporter=self.market_portfolio_stress_reporter,
            market_portfolio_stress_scenario_pipeline=self.market_portfolio_stress_scenario_pipeline,
            market_portfolio_tax_calculator=self.market_portfolio_tax_calculator,
            market_portfolio_telegram_command_center=self.market_portfolio_telegram_command_center,
            market_portfolio_telegram_notifier=self.market_portfolio_telegram_notifier,
            market_portfolio_valuation=self.market_portfolio_valuation,
            market_portfolio_var_liquidity_core=self.market_portfolio_var_liquidity_core,
            market_portfolio_visualizer_v2=self.market_portfolio_visualizer_v2,
            market_portfolio_webhook_event_logger=self.market_portfolio_webhook_event_logger,
            market_portfolio_webhook_sync=self.market_portfolio_webhook_sync,
            market_report_generator=self.market_report_generator,
            market_sentiment_digest=self.market_sentiment_digest,
            market_sentiment_risk_alert_bridge=self.market_sentiment_risk_alert_bridge,
            market_sentiment_risk_hub=self.market_sentiment_risk_hub,
            market_sentiment_telegram_publisher=self.market_sentiment_telegram_publisher,
            market_telegram_pipeline=self.market_telegram_pipeline
        )

    def test_compute_macro_liquidity_index_success(self):
        random_portfolio_id = uuid.uuid4().hex
        random_liquidity_score = round(random.uniform(10.0, 999.9), 4)

        self.market_portfolio_var_liquidity_core.calculate_core_liquidity.return_value = random_liquidity_score

        result = self.engine.compute_macro_liquidity_index(random_portfolio_id)

        self.market_portfolio_var_liquidity_core.calculate_core_liquidity.assert_called_once_with(random_portfolio_id)
        self.assertIn("liquidity_index", result)
        self.assertEqual(result["liquidity_index"], random_liquidity_score)
        self.assertEqual(result["portfolio_id"], random_portfolio_id)

    def test_stream_bytes_io_parsing(self):
        random_token = uuid.uuid4().hex.encode('utf-8')
        mock_stream = io.BytesIO(random_token)

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raw = mock_stream
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            random_url = f"https://{uuid.uuid4().hex}.com/api/v1/macro"
            parsed_data = self.engine.fetch_and_parse_raw_stream(random_url)

            self.assertIsNotNone(parsed_data)
            self.assertEqual(mock_stream.read(), b'')

    def test_market_anomaly_trigger_dispatch(self):
        random_anomaly_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
        random_threshold = random.randint(100, 5000)

        self.market_anomaly_detector.detect.return_value = {
            "code": random_anomaly_code,
            "threshold": random_threshold,
            "status": "TRIGGERED"
        }

        with patch('uuid.uuid4', return_value=uuid.UUID('12345678123456781234567812345678')):
            res = self.engine.evaluate_macro_anomalies(random_threshold)
            self.assertEqual(res["anomaly"]["code"], random_anomaly_code)
            self.market_portfolio_alert_dispatcher.dispatch.assert_called_once()

    def test_html_soup_scraping_integrity(self):
        random_id_tag = uuid.uuid4().hex
        html_payload = f"<html><body><div id='macro-target'>{random_id_tag}</div></body></html>"

        soup = BeautifulSoup(html_payload, 'html.parser')
        target_div = soup.find('div', id='macro-target')

        self.assertIsNotNone(target_div)
        self.assertEqual(target_div.text, random_id_tag)

    def test_error_propagation_no_silencing(self):
        random_error_msg = f"Fatal macro liquidity error: {uuid.uuid4().hex}"
        self.market_portfolio_var_liquidity_core.calculate_core_liquidity.side_effect = ValueError(random_error_msg)

        random_portfolio_id = uuid.uuid4().hex
        with self.assertRaises(ValueError) as ctx:
            self.engine.compute_macro_liquidity_index(random_portfolio_id)

        self.assertEqual(str(ctx.exception), random_error_msg)


if __name__ == '__main__':
    unittest.main()