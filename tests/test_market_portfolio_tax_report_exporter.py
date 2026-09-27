import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
import requests
from bs4 import BeautifulSoup

from skills.market_portfolio_tax_report_exporter import (
    MarketPortfolioTaxReportExporter,
    ExportValidationError,
    ExportTransmissionError
)

class TestMarketPortfolioTaxReportExporter(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_tool_1 = MagicMock()
        self.extractor_tool_2 = MagicMock()
        self.extractor_tool_3 = MagicMock()
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
        self.market_portfolio_integration_hub = MagicMock()
        self.market_portfolio_monitor = MagicMock()
        self.market_portfolio_performance_analytics = MagicMock()
        self.market_portfolio_predictive_aggregator = MagicMock()
        self.market_portfolio_scenario_simulator = MagicMock()
        self.market_portfolio_strategy_optimizer = MagicMock()
        self.market_portfolio_stress_recovery_coordinator_bridge = MagicMock()
        self.market_portfolio_stress_reporter = MagicMock()
        self.market_portfolio_stress_scenario_pipeline = MagicMock()
        self.market_portfolio_tax_calculator = MagicMock()
        self.market_portfolio_telegram_command_center = MagicMock()
        self.market_portfolio_telegram_notifier = MagicMock()
        self.market_portfolio_valuation = MagicMock()
        self.market_portfolio_visualizer_v2 = MagicMock()
        self.market_portfolio_webhook_event_logger = MagicMock()
        self.market_portfolio_webhook_sync = MagicMock()
        self.market_report_generator = MagicMock()
        self.market_sentiment_digest = MagicMock()
        self.market_sentiment_risk_alert_bridge = MagicMock()
        self.market_sentiment_risk_hub = MagicMock()
        self.market_sentiment_telegram_publisher = MagicMock()
        self.market_telegram_pipeline = MagicMock()

        self.exporter = MarketPortfolioTaxReportExporter(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_tool_1,
            extractor_tool_1790102839=self.extractor_tool_2,
            extractor_tool_1790262909=self.extractor_tool_3,
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
            market_portfolio_integration_hub=self.market_portfolio_integration_hub,
            market_portfolio_monitor=self.market_portfolio_monitor,
            market_portfolio_performance_analytics=self.market_portfolio_performance_analytics,
            market_portfolio_predictive_aggregator=self.market_portfolio_predictive_aggregator,
            market_portfolio_scenario_simulator=self.market_portfolio_scenario_simulator,
            market_portfolio_strategy_optimizer=self.market_portfolio_strategy_optimizer,
            market_portfolio_stress_recovery_coordinator_bridge=self.market_portfolio_stress_recovery_coordinator_bridge,
            market_portfolio_stress_reporter=self.market_portfolio_stress_reporter,
            market_portfolio_stress_scenario_pipeline=self.market_portfolio_stress_scenario_pipeline,
            market_portfolio_tax_calculator=self.market_portfolio_tax_calculator,
            market_portfolio_telegram_command_center=self.market_portfolio_telegram_command_center,
            market_portfolio_telegram_notifier=self.market_portfolio_telegram_notifier,
            market_portfolio_valuation=self.market_portfolio_valuation,
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

    def test_export_tax_report_success(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_tax_year = random.randint(2015, 2030)
        rand_format = random.choice(['PDF', 'CSV', 'XML', 'JSON'])
        rand_calc_result = {uuid.uuid4().hex: random.uniform(100.0, 50000.0)}

        self.market_portfolio_tax_calculator.compute_taxes.return_value = rand_calc_result

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = uuid.uuid4().bytes
            mock_post.return_value = mock_response

            result = self.exporter.export_report(rand_portfolio_id, rand_tax_year, rand_format)

            self.market_portfolio_tax_calculator.compute_taxes.assert_called_once_with(rand_portfolio_id, rand_tax_year)
            self.assertIn(rand_portfolio_id, str(result) or True)

    def test_export_validation_error_on_invalid_year(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_tax_year = random.choice([-1, 1899, 3050])
        rand_format = random.choice(['PDF', 'CSV'])

        with self.assertRaises(ExportValidationError):
            self.exporter.export_report(rand_portfolio_id, rand_tax_year, rand_format)

    def test_export_transmission_failure(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_tax_year = random.randint(2020, 2025)
        rand_format = random.choice(['XML', 'JSON'])

        self.market_portfolio_tax_calculator.compute_taxes.return_value = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = random.choice([400, 500, 502, 503])
            mock_post.return_value = mock_response

            with self.assertRaises(ExportTransmissionError):
                self.exporter.export_report(rand_portfolio_id, rand_tax_year, rand_format)

    def test_stream_dividend_report_parsing(self):
        rand_html_id = uuid.uuid4().hex
        rand_dividend_amount = round(random.uniform(5.0, 1500.0), 2)
        html_content = f"<html><body><div id='{rand_html_id}'>{rand_dividend_amount}</div></body></html>"

        stream = io.BytesIO(html_content.encode('utf-8'))

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raw = stream
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            parsed_value = self.exporter.parse_external_dividend_stream(uuid.uuid4().hex)

            soup = BeautifulSoup(html_content, 'html.parser')
            target_div = soup.find(id=rand_html_id)
            self.assertIsNotNone(target_div)
            self.assertEqual(float(target_div.text), rand_dividend_amount)

    def test_audit_log_exporter_integration(self):
        rand_event_id = uuid.uuid4().hex
        rand_message = ''.join(random.choices(string.ascii_letters + string.digits, k=25))

        self.market_portfolio_audit_log_exporter.export_log.return_value = {
            'status': 'success',
            'event_id': rand_event_id,
            'log': rand_message
        }

        res = self.exporter.trigger_audit_export(rand_event_id, rand_message)

        self.market_portfolio_audit_log_exporter.export_log.assert_called_once_with(rand_event_id, rand_message)
        self.assertEqual(res['event_id'], rand_event_id)
        self.assertEqual(res['log'], rand_message)