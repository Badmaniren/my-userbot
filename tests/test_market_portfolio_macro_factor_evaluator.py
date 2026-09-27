import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import requests
from bs4 import BeautifulSoup

from skills.market_portfolio_macro_factor_evaluator import (
    MarketPortfolioMacroFactorEvaluator
)

class TestMarketPortfolioMacroFactorEvaluator(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_1 = MagicMock()
        self.extractor_2 = MagicMock()
        self.extractor_3 = MagicMock()
        self.anomaly_detector = MagicMock()
        self.insider_tracker = MagicMock()
        self.insider_alert = MagicMock()
        self.news_sentiment = MagicMock()
        self.market_parser = MagicMock()
        self.alert_dispatcher = MagicMock()
        self.alert_event_sink = MagicMock()
        self.alert_filter_router = MagicMock()
        self.api_gateway = MagicMock()
        self.audit_notifier = MagicMock()
        self.audit_compliance = MagicMock()
        self.audit_log_exporter = MagicMock()
        self.autonomous_sentinel = MagicMock()
        self.backtest_bridge = MagicMock()
        self.backtester = MagicMock()
        self.collector_agent = MagicMock()
        self.data_exporter = MagicMock()
        self.digest = MagicMock()
        self.event_intelligence = MagicMock()
        self.integration_hub = MagicMock()
        self.monitor = MagicMock()
        self.performance_analytics = MagicMock()
        self.predictive_aggregator = MagicMock()
        self.scenario_simulator = MagicMock()
        self.strategy_optimizer = MagicMock()
        self.stress_reporter = MagicMock()
        self.stress_pipeline = MagicMock()
        self.telegram_command = MagicMock()
        self.telegram_notifier = MagicMock()
        self.valuation = MagicMock()
        self.visualizer = MagicMock()
        self.webhook_logger = MagicMock()
        self.webhook_sync = MagicMock()
        self.report_generator = MagicMock()
        self.sentiment_digest = MagicMock()
        self.sentiment_risk_bridge = MagicMock()
        self.sentiment_risk_hub = MagicMock()
        self.sentiment_telegram = MagicMock()
        self.telegram_pipeline = MagicMock()

        self.evaluator = MarketPortfolioMacroFactorEvaluator(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_1,
            extractor_tool_1790102839=self.extractor_2,
            extractor_tool_1790262909=self.extractor_3,
            market_anomaly_detector=self.anomaly_detector,
            market_insider_activity_tracker=self.insider_tracker,
            market_insider_alert_pipeline=self.insider_alert,
            market_news_sentiment_analyzer=self.news_sentiment,
            market_parser=self.market_parser,
            market_portfolio_alert_dispatcher=self.alert_dispatcher,
            market_portfolio_alert_event_sink=self.alert_event_sink,
            market_portfolio_alert_filter_router=self.alert_filter_router,
            market_portfolio_api_gateway=self.api_gateway,
            market_portfolio_audit_alert_notifier=self.audit_notifier,
            market_portfolio_audit_compliance_hub=self.audit_compliance,
            market_portfolio_audit_log_exporter=self.audit_log_exporter,
            market_portfolio_autonomous_sentinel=self.autonomous_sentinel,
            market_portfolio_backtest_evaluator_bridge=self.backtest_bridge,
            market_portfolio_backtester=self.backtester,
            market_portfolio_collector_agent=self.collector_agent,
            market_portfolio_data_exporter=self.data_exporter,
            market_portfolio_digest=self.digest,
            market_portfolio_event_intelligence_hub=self.event_intelligence,
            market_portfolio_integration_hub=self.integration_hub,
            market_portfolio_monitor=self.monitor,
            market_portfolio_performance_analytics=self.performance_analytics,
            market_portfolio_predictive_aggregator=self.predictive_aggregator,
            market_portfolio_scenario_simulator=self.scenario_simulator,
            market_portfolio_strategy_optimizer=self.strategy_optimizer,
            market_portfolio_stress_reporter=self.stress_reporter,
            market_portfolio_stress_scenario_pipeline=self.stress_pipeline,
            market_portfolio_telegram_command_center=self.telegram_command,
            market_portfolio_telegram_notifier=self.telegram_notifier,
            market_portfolio_valuation=self.valuation,
            market_portfolio_visualizer_v2=self.visualizer,
            market_portfolio_webhook_event_logger=self.webhook_logger,
            market_portfolio_webhook_sync=self.webhook_sync,
            market_report_generator=self.report_generator,
            market_sentiment_digest=self.sentiment_digest,
            market_sentiment_risk_alert_bridge=self.sentiment_risk_bridge,
            market_sentiment_risk_hub=self.sentiment_risk_hub,
            market_sentiment_telegram_publisher=self.sentiment_telegram,
            market_telegram_pipeline=self.telegram_pipeline
        )

    def test_evaluate_macro_factors_success(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_inflation = round(random.uniform(1.0, 15.0), 2)
        rand_rate = round(random.uniform(0.0, 10.0), 2)
        rand_currency = "".join(random.choices(string.ascii_uppercase, k=3))

        self.db_storage.get_portfolio.return_value = {
            "id": rand_portfolio_id,
            "assets": [uuid.uuid4().hex for _ in range(random.randint(1, 5))]
        }
        self.extractor_1.extract.return_value = {"inflation": rand_inflation}
        self.extractor_2.extract.return_value = {"interest_rate": rand_rate}
        self.extractor_3.extract.return_value = {"currency": rand_currency}

        result = self.evaluator.evaluate(rand_portfolio_id)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], rand_portfolio_id)
        self.assertEqual(result["macro_factors"]["inflation"], rand_inflation)
        self.assertEqual(result["macro_factors"]["interest_rate"], rand_rate)
        self.assertEqual(result["macro_factors"]["currency"], rand_currency)
        self.db_storage.get_portfolio.assert_called_once_with(rand_portfolio_id)

    def test_evaluate_with_stream_data_parsing(self):
        rand_stream_id = uuid.uuid4().hex
        random_bytes = f"DATA_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(random_bytes)

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = random_bytes
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            self.market_parser.parse_stream.return_value = {
                "stream_id": rand_stream_id,
                "parsed_payload": mock_stream.read().decode('utf-8')
            }

            result = self.evaluator.evaluate_from_stream(rand_stream_id, f"https://{uuid.uuid4().hex}.com/feed")
            self.assertEqual(result["stream_id"], rand_stream_id)
            self.assertIn(rand_stream_id, result["stream_id"])
            self.market_parser.parse_stream.assert_called_once()

    def test_macro_anomaly_trigger(self):
        rand_anomaly_code = uuid.uuid4().hex
        rand_threshold = random.uniform(50.0, 100.0)

        self.anomaly_detector.check_anomaly.return_value = {
            "is_anomaly": True,
            "code": rand_anomaly_code,
            "score": rand_threshold
        }

        with patch('random.randint', return_value=42):
            alert_res = self.evaluator.handle_macro_anomalies(uuid.uuid4().hex)

        self.assertTrue(alert_res["triggered"])
        self.assertEqual(alert_res["anomaly_code"], rand_anomaly_code)
        self.alert_dispatcher.dispatch.assert_called_once()

    def test_html_soup_parsing_in_evaluator(self):
        rand_tag_id = uuid.uuid4().hex
        rand_html = f"<html><body><div id='{rand_tag_id}'>MacroData</div></body></html>"

        soup = BeautifulSoup(rand_html, 'html.parser')
        extracted_text = soup.find(id=rand_tag_id).text

        self.assertEqual(extracted_text, "MacroData")
        self.market_parser.extract_html_data.return_value = extracted_text

        res = self.evaluator.parse_macro_html(rand_html)
        self.assertEqual(res, "MacroData")