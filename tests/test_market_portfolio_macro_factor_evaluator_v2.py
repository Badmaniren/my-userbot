import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
import requests
from bs4 import BeautifulSoup

from skills.market_portfolio_macro_factor_evaluator_v2 import (
    MacroFactorEvaluatorV2,
    MacroEvaluationError,
    MacroDataFetchError
)

class TestMacroFactorEvaluatorV2(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_1 = MagicMock()
        self.extractor_2 = MagicMock()
        self.extractor_3 = MagicMock()
        self.extractor_4 = MagicMock()
        self.anomaly_detector = MagicMock()
        self.insider_tracker = MagicMock()
        self.alert_pipeline = MagicMock()
        self.anomaly_analyzer = MagicMock()
        self.anomaly_report_bridge = MagicMock()
        self.sentiment_analyzer = MagicMock()
        self.market_parser = MagicMock()
        self.alert_dispatcher = MagicMock()
        self.event_sink = MagicMock()
        self.filter_router = MagicMock()
        self.api_gateway = MagicMock()
        self.audit_notifier = MagicMock()
        self.compliance_hub = MagicMock()
        self.log_exporter = MagicMock()
        self.autonomous_sentinel = MagicMock()
        self.backtest_bridge = MagicMock()
        self.backtester = MagicMock()
        self.collector_agent = MagicMock()
        self.data_exporter = MagicMock()
        self.digest = MagicMock()
        self.dividend_tracker = MagicMock()
        self.event_intelligence_hub = MagicMock()
        self.execution_cost_optimizer = MagicMock()
        self.execution_pipeline = MagicMock()
        self.integration_hub = MagicMock()
        self.monitor = MagicMock()
        self.performance_analytics = MagicMock()
        self.predictive_aggregator = MagicMock()
        self.scenario_simulator = MagicMock()
        self.slippage_model = MagicMock()
        self.strategy_optimizer = MagicMock()
        self.stress_audit_visualizer = MagicMock()
        self.stress_monte_carlo_engine = MagicMock()
        self.stress_recovery_coordinator_bridge = MagicMock()
        self.stress_reporter = MagicMock()
        self.stress_scenario_pipeline = MagicMock()
        self.tax_calculator = MagicMock()
        self.telegram_command_center = MagicMock()
        self.telegram_notifier = MagicMock()
        self.valuation = MagicMock()
        self.var_liquidity_core = MagicMock()
        self.visualizer_v2 = MagicMock()
        self.webhook_event_logger = MagicMock()
        self.webhook_sync = MagicMock()
        self.report_generator = MagicMock()
        self.sentiment_digest = MagicMock()
        self.sentiment_risk_alert_bridge = MagicMock()
        self.sentiment_risk_hub = MagicMock()
        self.sentiment_telegram_publisher = MagicMock()
        self.telegram_pipeline = MagicMock()

        self.evaluator = MacroFactorEvaluatorV2(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_1,
            extractor_tool_1790102839=self.extractor_2,
            extractor_tool_1790262909=self.extractor_3,
            extractor_tool_1790621808=self.extractor_4,
            market_anomaly_detector=self.anomaly_detector,
            market_insider_activity_tracker=self.insider_tracker,
            market_insider_alert_pipeline=self.alert_pipeline,
            market_insider_anomaly_analyzer=self.anomaly_analyzer,
            market_insider_anomaly_report_bridge=self.anomaly_report_bridge,
            market_news_sentiment_analyzer=self.sentiment_analyzer,
            market_parser=self.market_parser,
            market_portfolio_alert_dispatcher=self.alert_dispatcher,
            market_portfolio_alert_event_sink=self.event_sink,
            market_portfolio_alert_filter_router=self.filter_router,
            market_portfolio_api_gateway=self.api_gateway,
            market_portfolio_audit_alert_notifier=self.audit_notifier,
            market_portfolio_audit_compliance_hub=self.compliance_hub,
            market_portfolio_audit_log_exporter=self.log_exporter,
            market_portfolio_autonomous_sentinel=self.autonomous_sentinel,
            market_portfolio_backtest_evaluator_bridge=self.backtest_bridge,
            market_portfolio_backtester=self.backtester,
            market_portfolio_collector_agent=self.collector_agent,
            market_portfolio_data_exporter=self.data_exporter,
            market_portfolio_digest=self.digest,
            market_portfolio_dividend_tracker=self.dividend_tracker,
            market_portfolio_event_intelligence_hub=self.event_intelligence_hub,
            market_portfolio_execution_cost_optimizer=self.execution_cost_optimizer,
            market_portfolio_execution_pipeline=self.execution_pipeline,
            market_portfolio_integration_hub=self.integration_hub,
            market_portfolio_monitor=self.monitor,
            market_portfolio_performance_analytics=self.performance_analytics,
            market_portfolio_predictive_aggregator=self.predictive_aggregator,
            market_portfolio_scenario_simulator=self.scenario_simulator,
            market_portfolio_slippage_model=self.slippage_model,
            market_portfolio_strategy_optimizer=self.strategy_optimizer,
            market_portfolio_stress_audit_visualizer=self.stress_audit_visualizer,
            market_portfolio_stress_monte_carlo_engine=self.stress_monte_carlo_engine,
            market_portfolio_stress_recovery_coordinator_bridge=self.stress_recovery_coordinator_bridge,
            market_portfolio_stress_reporter=self.stress_reporter,
            market_portfolio_stress_scenario_pipeline=self.stress_scenario_pipeline,
            market_portfolio_tax_calculator=self.tax_calculator,
            market_portfolio_telegram_command_center=self.telegram_command_center,
            market_portfolio_telegram_notifier=self.telegram_notifier,
            market_portfolio_valuation=self.valuation,
            market_portfolio_var_liquidity_core=self.var_liquidity_core,
            market_portfolio_visualizer_v2=self.visualizer_v2,
            market_portfolio_webhook_event_logger=self.webhook_event_logger,
            market_portfolio_webhook_sync=self.webhook_sync,
            market_report_generator=self.report_generator,
            market_sentiment_digest=self.sentiment_digest,
            market_sentiment_risk_alert_bridge=self.sentiment_risk_alert_bridge,
            market_sentiment_risk_hub=self.sentiment_risk_hub,
            market_sentiment_telegram_publisher=self.sentiment_telegram_publisher,
            market_telegram_pipeline=self.telegram_pipeline
        )

    def test_evaluate_macro_factors_success(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_factor_name = "".join(random.choices(string.ascii_letters, k=12))
        rand_score = random.uniform(1.0, 100.0)

        self.collector_agent.collect.return_value = {rand_factor_name: rand_score}
        self.scenario_simulator.simulate.return_value = {rand_portfolio_id: rand_score * 0.9}

        result = self.evaluator.evaluate_macro_factors(rand_portfolio_id)

        self.assertIsInstance(result, dict)
        self.assertIn("evaluation_score", result)
        self.assertEqual(result["portfolio_id"], rand_portfolio_id)
        self.db_storage.save.assert_called_once()

    def test_evaluate_macro_factors_fetch_error(self):
        rand_portfolio_id = uuid.uuid4().hex
        self.collector_agent.collect.side_effect = requests.RequestException(uuid.uuid4().hex)

        with self.assertRaises(MacroDataFetchError):
            self.evaluator.evaluate_macro_factors(rand_portfolio_id)

    def test_stream_processing_with_bytes_io(self):
        rand_stream_data = "".join(random.choices(string.ascii_letters, k=64)).encode("utf-8")
        stream_mock = io.BytesIO(rand_stream_data)

        with patch('skills.market_portfolio_macro_factor_evaluator_v2.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raw = stream_mock
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            rand_url = f"https://{uuid.uuid4().hex}.com/api/stream"
            processed_data = self.evaluator.process_external_stream(rand_url)

            self.assertEqual(processed_data, rand_stream_data)

    def test_anomaly_detection_trigger(self):
        rand_anomaly_id = uuid.uuid4().hex
        rand_threshold = random.uniform(0.1, 0.9)

        self.anomaly_detector.detect.return_value = {"anomaly_id": rand_anomaly_id, "triggered": True}

        with patch.object(self.alert_dispatcher, 'dispatch') as mock_dispatch:
            self.evaluator.check_and_dispatch_anomalies(rand_threshold)
            mock_dispatch.assert_called_once()
            args, _ = mock_dispatch.call_args
            self.assertEqual(args[0]["anomaly_id"], rand_anomaly_id)

    def test_parser_integration_with_soup(self):
        rand_text = uuid.uuid4().hex
        html_content = f"<html><body><div class='macro-data'>{rand_text}</div></body></html>"

        soup = BeautifulSoup(html_content, 'html.parser')
        self.market_parser.parse.return_value = soup

        rand_url = f"https://{uuid.uuid4().hex}.org/data"
        extracted_value = self.evaluator.extract_parsed_macro_metric(rand_url)

        self.assertEqual(extracted_value, rand_text)

    def test_fallback_evaluation_on_exception(self):
        rand_portfolio_id = uuid.uuid4().hex
        self.scenario_simulator.simulate.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(MacroEvaluationError):
            self.evaluator.evaluate_macro_factors(rand_portfolio_id)

        self.audit_notifier.notify.assert_called()
