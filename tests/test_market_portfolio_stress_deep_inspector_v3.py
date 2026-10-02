import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string

from skills.market_portfolio_stress_deep_inspector_v3 import (
    MarketPortfolioStressDeepInspectorV3,
    StressInspectionError
)


class TestMarketPortfolioStressDeepInspectorV3(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_1 = MagicMock()
        self.extractor_2 = MagicMock()
        self.extractor_3 = MagicMock()
        self.extractor_4 = MagicMock()
        self.anomaly_detector = MagicMock()
        self.insider_tracker = MagicMock()
        self.insider_alert_pipeline = MagicMock()
        self.insider_anomaly_analyzer = MagicMock()
        self.insider_report_bridge = MagicMock()
        self.news_analyzer = MagicMock()
        self.market_parser = MagicMock()
        self.alert_dispatcher = MagicMock()
        self.alert_event_sink = MagicMock()
        self.alert_filter_router = MagicMock()
        self.api_gateway = MagicMock()
        self.audit_notifier = MagicMock()
        self.audit_compliance_hub = MagicMock()
        self.audit_log_exporter = MagicMock()
        self.autonomous_sentinel = MagicMock()
        self.backtest_evaluator_bridge = MagicMock()
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
        self.monte_carlo_engine = MagicMock()
        self.recovery_coordinator_bridge = MagicMock()
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

        self.inspector = MarketPortfolioStressDeepInspectorV3(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_1,
            extractor_tool_1790102839=self.extractor_2,
            extractor_tool_1790262909=self.extractor_3,
            extractor_tool_1790621808=self.extractor_4,
            market_anomaly_detector=self.anomaly_detector,
            market_insider_activity_tracker=self.insider_tracker,
            market_insider_alert_pipeline=self.insider_alert_pipeline,
            market_insider_anomaly_analyzer=self.insider_anomaly_analyzer,
            market_insider_anomaly_report_bridge=self.insider_report_bridge,
            market_news_sentiment_analyzer=self.news_analyzer,
            market_parser=self.market_parser,
            market_portfolio_alert_dispatcher=self.alert_dispatcher,
            market_portfolio_alert_event_sink=self.alert_event_sink,
            market_portfolio_alert_filter_router=self.alert_filter_router,
            market_portfolio_api_gateway=self.api_gateway,
            market_portfolio_audit_alert_notifier=self.audit_notifier,
            market_portfolio_audit_compliance_hub=self.audit_compliance_hub,
            market_portfolio_audit_log_exporter=self.audit_log_exporter,
            market_portfolio_autonomous_sentinel=self.autonomous_sentinel,
            market_portfolio_backtest_evaluator_bridge=self.backtest_evaluator_bridge,
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
            market_portfolio_stress_monte_carlo_engine=self.monte_carlo_engine,
            market_portfolio_stress_recovery_coordinator_bridge=self.recovery_coordinator_bridge,
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

    def test_inspect_portfolio_vulnerability_success(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_scenario_name = "".join(random.choices(string.ascii_letters, k=12))
        rand_threshold = random.uniform(0.01, 0.99)
        expected_risk_score = random.uniform(1.0, 100.0)

        self.monte_carlo_engine.run_simulation.return_value = {
            "portfolio_id": rand_portfolio_id,
            "risk_score": expected_risk_score
        }

        result = self.inspector.inspect_vulnerability(
            portfolio_id=rand_portfolio_id,
            scenario=rand_scenario_name,
            threshold=rand_threshold
        )

        self.assertEqual(result["portfolio_id"], rand_portfolio_id)
        self.assertEqual(result["risk_score"], expected_risk_score)
        self.monte_carlo_engine.run_simulation.assert_called_once_with(
            portfolio_id=rand_portfolio_id,
            scenario=rand_scenario_name,
            threshold=rand_threshold
        )

    def test_inspect_portfolio_vulnerability_with_stream_data(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_stream_payload = uuid.uuid4().bytes + bytes(random.choices(b"abcdef", k=32))
        stream_mock = io.BytesIO(rand_stream_payload)

        self.market_parser.parse_stream.return_value = {
            "parsed_payload": rand_stream_payload.hex()
        }

        result = self.inspector.inspect_stream_vulnerability(
            portfolio_id=rand_portfolio_id,
            data_stream=stream_mock
        )

        self.assertEqual(result["parsed_payload"], rand_stream_payload.hex())
        self.market_parser.parse_stream.assert_called_once()

    def test_inspect_vulnerability_raises_custom_error_on_failure(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_scenario = "".join(random.choices(string.ascii_lowercase, k=8))

        self.scenario_simulator.simulate.side_effect = RuntimeError("Critical System Crash")

        with self.assertRaises(StressInspectionError):
            self.inspector.inspect_vulnerability(
                portfolio_id=rand_portfolio_id,
                scenario=rand_scenario,
                threshold=0.5
            )

    def test_deep_inspection_pipeline_execution(self):
        rand_token = uuid.uuid4().hex
        rand_factor = random.randint(10, 1000)

        self.stress_scenario_pipeline.execute.return_value = {
            "token": rand_token,
            "factor": rand_factor,
            "status": "COMPLETED"
        }

        with patch("skills.market_portfolio_stress_deep_inspector_v3.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value.hex = rand_token
            res = self.inspector.run_deep_pipeline(rand_factor)

            self.assertEqual(res["token"], rand_token)
            self.assertEqual(res["factor"], rand_factor)
            self.assertEqual(res["status"], "COMPLETED")


if __name__ == "__main__":
    unittest.main()