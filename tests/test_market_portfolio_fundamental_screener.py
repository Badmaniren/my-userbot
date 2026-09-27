import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
from skills.market_portfolio_fundamental_screener import MarketPortfolioFundamentalScreener

class TestMarketPortfolioFundamentalScreener(unittest.TestCase):
    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_1 = MagicMock()
        self.extractor_2 = MagicMock()
        self.extractor_3 = MagicMock()
        self.anomaly_detector = MagicMock()
        self.insider_tracker = MagicMock()
        self.insider_alert = MagicMock()
        self.insider_anomaly = MagicMock()
        self.insider_report_bridge = MagicMock()
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
        self.dividend_tracker = MagicMock()
        self.event_hub = MagicMock()
        self.integration_hub = MagicMock()
        self.monitor = MagicMock()
        self.performance_analytics = MagicMock()
        self.predictive_aggregator = MagicMock()
        self.scenario_simulator = MagicMock()
        self.strategy_optimizer = MagicMock()
        self.stress_recovery = MagicMock()
        self.stress_reporter = MagicMock()
        self.stress_pipeline = MagicMock()
        self.tax_calculator = MagicMock()
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

        self.screener = MarketPortfolioFundamentalScreener(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_1,
            extractor_tool_1790102839=self.extractor_2,
            extractor_tool_1790262909=self.extractor_3,
            market_anomaly_detector=self.anomaly_detector,
            market_insider_activity_tracker=self.insider_tracker,
            market_insider_alert_pipeline=self.insider_alert,
            market_insider_anomaly_analyzer=self.insider_anomaly,
            market_insider_anomaly_report_bridge=self.insider_report_bridge,
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
            market_portfolio_dividend_tracker=self.dividend_tracker,
            market_portfolio_event_intelligence_hub=self.event_hub,
            market_portfolio_integration_hub=self.integration_hub,
            market_portfolio_monitor=self.monitor,
            market_portfolio_performance_analytics=self.performance_analytics,
            market_portfolio_predictive_aggregator=self.predictive_aggregator,
            market_portfolio_scenario_simulator=self.scenario_simulator,
            market_portfolio_strategy_optimizer=self.strategy_optimizer,
            market_portfolio_stress_recovery_coordinator_bridge=self.stress_recovery,
            market_portfolio_stress_reporter=self.stress_reporter,
            market_portfolio_stress_scenario_pipeline=self.stress_pipeline,
            market_portfolio_tax_calculator=self.tax_calculator,
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

    def test_calculate_multipliers_and_filter(self):
        rand_ticker = ''.join(random.choices(string.ascii_uppercase, k=5))
        rand_pe = round(random.uniform(5.0, 35.0), 2)
        rand_pb = round(random.uniform(0.5, 5.0), 2)
        rand_ps = round(random.uniform(0.1, 10.0), 2)
        rand_de = round(random.uniform(0.1, 2.5), 2)

        raw_financial_bytes = f"ticker:{rand_ticker},pe:{rand_pe},pb:{rand_pb},ps:{rand_ps},de:{rand_de}".encode('utf-8')
        mock_stream = io.BytesIO(raw_financial_bytes)

        max_pe_threshold = rand_pe + 5.0
        max_de_threshold = rand_de + 1.0

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = mock_stream.read()
            mock_get.return_value = mock_response

            result = self.screener.evaluate_and_filter(
                ticker=rand_ticker,
                max_pe=max_pe_threshold,
                max_de=max_de_threshold
            )

            self.assertIn(rand_ticker, [res.get('ticker') for res in result] if isinstance(result, list) else [result.get('ticker')])

            filtered_item = result[0] if isinstance(result, list) else result
            self.assertEqual(filtered_item['ticker'], rand_ticker)
            self.assertAlmostEqual(filtered_item['pe'], rand_pe)
            self.assertAlmostEqual(filtered_item['de'], rand_de)

    def test_screener_rejects_unstable_assets(self):
        rand_ticker = ''.join(random.choices(string.ascii_uppercase, k=4))
        bad_pe = round(random.uniform(50.0, 150.0), 2)
        bad_de = round(random.uniform(3.0, 10.0), 2)

        strict_max_pe = 20.0
        strict_max_de = 1.5

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = f"ticker:{rand_ticker},pe:{bad_pe},de:{bad_de}".encode('utf-8')
            mock_get.return_value = mock_response

            result = self.screener.evaluate_and_filter(
                ticker=rand_ticker,
                max_pe=strict_max_pe,
                max_de=strict_max_de
            )

            if isinstance(result, list):
                self.assertEqual(len(result), 0)
            else:
                self.assertFalse(result.get('passed', False))

if __name__ == '__main__':
    unittest.main()