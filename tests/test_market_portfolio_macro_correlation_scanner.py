import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
import requests
from bs4 import BeautifulSoup

from skills.market_portfolio_macro_correlation_scanner import (
    MarketPortfolioMacroCorrelationScanner
)

class TestMarketPortfolioMacroCorrelationScanner(unittest.TestCase):

    def setUp(self):
        self.rand_db = f"sqlite:///:memory:?cache=shared&uuid={uuid.uuid4().hex}"
        self.rand_api_key = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        
        self.mock_db = MagicMock()
        self.mock_extractor_1 = MagicMock()
        self.mock_extractor_2 = MagicMock()
        self.mock_extractor_3 = MagicMock()
        self.mock_extractor_4 = MagicMock()
        self.mock_anomaly_detector = MagicMock()
        self.mock_insider_tracker = MagicMock()
        self.mock_alert_pipeline = MagicMock()
        self.mock_anomaly_analyzer = MagicMock()
        self.mock_report_bridge = MagicMock()
        self.mock_sentiment_analyzer = MagicMock()
        self.mock_parser = MagicMock()
        self.mock_dispatcher = MagicMock()
        self.mock_event_sink = MagicMock()
        self.mock_filter_router = MagicMock()
        self.mock_api_gateway = MagicMock()
        self.mock_audit_notifier = MagicMock()
        self.mock_compliance_hub = MagicMock()
        self.mock_log_exporter = MagicMock()
        self.mock_sentinel = MagicMock()
        self.mock_backtest_bridge = MagicMock()
        self.mock_backtester = MagicMock()
        self.mock_collector = MagicMock()
        self.mock_data_exporter = MagicMock()
        self.mock_digest = MagicMock()
        self.mock_dividend_tracker = MagicMock()
        self.mock_event_hub = MagicMock()
        self.mock_exec_optimizer = MagicMock()
        self.mock_exec_pipeline = MagicMock()
        self.mock_integration_hub = MagicMock()
        self.mock_liquidity_analyzer = MagicMock()
        self.mock_monitor = MagicMock()
        self.mock_performance_analytics = MagicMock()
        self.mock_predictive_aggregator = MagicMock()
        self.mock_scenario_simulator = MagicMock()
        self.mock_slippage_model = MagicMock()
        self.mock_strategy_optimizer = MagicMock()
        self.mock_stress_visualizer = MagicMock()
        self.mock_monte_carlo = MagicMock()
        self.mock_recovery_coordinator = MagicMock()
        self.mock_stress_reporter = MagicMock()
        self.mock_stress_pipeline = MagicMock()
        self.mock_tax_calculator = MagicMock()
        self.mock_telegram_cmd = MagicMock()
        self.mock_telegram_notifier = MagicMock()
        self.mock_valuation = MagicMock()
        self.mock_var_liquidity = MagicMock()
        self.mock_visualizer_v2 = MagicMock()
        self.mock_webhook_logger = MagicMock()
        self.mock_webhook_sync = MagicMock()
        self.mock_report_generator = MagicMock()
        self.mock_sentiment_digest = MagicMock()
        self.mock_sentiment_risk_bridge = MagicMock()
        self.mock_sentiment_risk_hub = MagicMock()
        self.mock_telegram_publisher = MagicMock()
        self.mock_telegram_pipeline = MagicMock()

        self.scanner = MarketPortfolioMacroCorrelationScanner(
            db_storage=self.mock_db,
            extractor_tool_1790087207=self.mock_extractor_1,
            extractor_tool_1790102839=self.mock_extractor_2,
            extractor_tool_1790262909=self.mock_extractor_3,
            extractor_tool_1790621808=self.mock_extractor_4,
            market_anomaly_detector=self.mock_anomaly_detector,
            market_insider_activity_tracker=self.mock_insider_tracker,
            market_insider_alert_pipeline=self.mock_alert_pipeline,
            market_insider_anomaly_analyzer=self.mock_anomaly_analyzer,
            market_insider_anomaly_report_bridge=self.mock_report_bridge,
            market_news_sentiment_analyzer=self.mock_sentiment_analyzer,
            market_parser=self.mock_parser,
            market_portfolio_alert_dispatcher=self.mock_dispatcher,
            market_portfolio_alert_event_sink=self.mock_event_sink,
            market_portfolio_alert_filter_router=self.mock_filter_router,
            market_portfolio_api_gateway=self.mock_api_gateway,
            market_portfolio_audit_alert_notifier=self.mock_audit_notifier,
            market_portfolio_audit_compliance_hub=self.mock_compliance_hub,
            market_portfolio_audit_log_exporter=self.mock_log_exporter,
            market_portfolio_autonomous_sentinel=self.mock_sentinel,
            market_portfolio_backtest_evaluator_bridge=self.mock_backtest_bridge,
            market_portfolio_backtester=self.mock_backtester,
            market_portfolio_collector_agent=self.mock_collector,
            market_portfolio_data_exporter=self.mock_data_exporter,
            market_portfolio_digest=self.mock_digest,
            market_portfolio_dividend_tracker=self.mock_dividend_tracker,
            market_portfolio_event_intelligence_hub=self.mock_event_hub,
            market_portfolio_execution_cost_optimizer=self.mock_exec_optimizer,
            market_portfolio_execution_pipeline=self.mock_exec_pipeline,
            market_portfolio_integration_hub=self.mock_integration_hub,
            market_portfolio_liquidity_scenario_analyzer=self.mock_liquidity_analyzer,
            market_portfolio_monitor=self.mock_monitor,
            market_portfolio_performance_analytics=self.mock_performance_analytics,
            market_portfolio_predictive_aggregator=self.mock_predictive_aggregator,
            market_portfolio_scenario_simulator=self.mock_scenario_simulator,
            market_portfolio_slippage_model=self.mock_slippage_model,
            market_portfolio_strategy_optimizer=self.mock_strategy_optimizer,
            market_portfolio_stress_audit_visualizer=self.mock_stress_visualizer,
            market_portfolio_stress_monte_carlo_engine=self.mock_monte_carlo,
            market_portfolio_stress_recovery_coordinator_bridge=self.mock_recovery_coordinator,
            market_portfolio_stress_reporter=self.mock_stress_reporter,
            market_portfolio_stress_scenario_pipeline=self.mock_stress_pipeline,
            market_portfolio_tax_calculator=self.mock_tax_calculator,
            market_portfolio_telegram_command_center=self.mock_telegram_cmd,
            market_portfolio_telegram_notifier=self.mock_telegram_notifier,
            market_portfolio_valuation=self.mock_valuation,
            market_portfolio_var_liquidity_core=self.mock_var_liquidity,
            market_portfolio_visualizer_v2=self.mock_visualizer_v2,
            market_portfolio_webhook_event_logger=self.mock_webhook_logger,
            market_portfolio_webhook_sync=self.mock_webhook_sync,
            market_report_generator=self.mock_report_generator,
            market_sentiment_digest=self.mock_sentiment_digest,
            market_sentiment_risk_alert_bridge=self.mock_sentiment_risk_bridge,
            market_sentiment_risk_hub=self.mock_sentiment_risk_hub,
            market_sentiment_telegram_publisher=self.mock_telegram_publisher,
            market_telegram_pipeline=self.mock_telegram_pipeline
        )

    def test_scan_macro_correlations_success(self):
        unique_portfolio_id = uuid.uuid4().hex
        expected_correlation_coefficient = round(random.uniform(-1.0, 1.0), 4)
        
        self.mock_extractor_1.extract.return_value = {"portfolio_id": unique_portfolio_id, "macro_factor": "CPI"}
        self.mock_anomaly_detector.detect.return_value = {"correlation": expected_correlation_coefficient, "risk_flag": True}

        result = self.scanner.scan_macro_correlations(unique_portfolio_id)

        self.assertIn("correlation", result)
        self.assertEqual(result["correlation"], expected_correlation_coefficient)
        self.mock_extractor_1.extract.assert_called_once_with(unique_portfolio_id)
        self.mock_anomaly_detector.detect.assert_called_once()

    def test_parse_external_macro_stream_with_bytes_io(self):
        random_bytes = f"macro_stream_data_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(random_bytes)

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raw = mock_stream
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            url = f"https://macro-feed-{uuid.uuid4().hex}.internal/stream"
            result = self.scanner.parse_external_macro_stream(url)

            self.assertTrue(result)
            mock_get.assert_called_once_with(url, stream=True)

    def test_hidden_systemic_risk_detection_flow(self):
        risk_token = f"risk_{uuid.uuid4().hex}"
        self.mock_stress_pipeline.run.return_value = {"status": "critical", "token": risk_token}
        self.mock_dispatcher.dispatch.return_value = True

        status = self.scanner.evaluate_systemic_risks(risk_token)

        self.assertEqual(status["token"], risk_token)
        self.assertEqual(status["status"], "critical")
        self.mock_stress_pipeline.run.assert_called_once_with(risk_token)
        self.mock_dispatcher.dispatch.assert_called_once()

    def test_soup_parsing_macro_html(self):
        random_id = uuid.uuid4().hex
        html_content = f"<html><body><div id='macro-metric-{random_id}'>0.88</div></body></html>"
        
        soup = BeautifulSoup(html_content, 'html.parser')
        metric_div = soup.find(id=f"macro-metric-{random_id}")
        
        self.assertIsNotNone(metric_div)
        self.assertEqual(metric_div.text, "0.88")

    def test_audit_log_exporter_integration(self):
        export_id = uuid.uuid4().hex
        self.mock_log_exporter.export.return_value = {"export_id": export_id, "success": True}

        res = self.scanner.export_audit_logs(export_id)

        self.assertTrue(res["success"])
        self.assertEqual(res["export_id"], export_id)
        self.mock_log_exporter.export.assert_called_once_with(export_id)