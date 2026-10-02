import unittest
import uuid
import json
import os
import random
import io
from unittest.mock import MagicMock, patch
from skills.market_portfolio_macro_liquidity_aggregator import MarketPortfolioMacroLiquidityAggregator

class TestMarketPortfolioMacroLiquidityAggregator(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_core = MagicMock()
        self.mock_notifier = MagicMock()
        self.mock_extractor = MagicMock()

        # Инициализация с минимально необходимыми зависимостями для теста
        self.aggregator = MarketPortfolioMacroLiquidityAggregator(
            db_storage=self.mock_db,
            extractor_tool_1790087207=self.mock_extractor,
            extractor_tool_1790102839=None,
            extractor_tool_1790262909=None,
            extractor_tool_1790621808=None,
            market_anomaly_detector=None,
            market_insider_activity_tracker=None,
            market_insider_alert_pipeline=None,
            market_insider_anomaly_analyzer=None,
            market_insider_anomaly_report_bridge=None,
            market_news_sentiment_analyzer=None,
            market_parser=None,
            market_portfolio_alert_dispatcher=None,
            market_portfolio_alert_event_sink=None,
            market_portfolio_alert_filter_router=None,
            market_portfolio_api_gateway=None,
            market_portfolio_audit_alert_notifier=self.mock_notifier,
            market_portfolio_audit_compliance_hub=None,
            market_portfolio_audit_log_exporter=None,
            market_portfolio_autonomous_sentinel=None,
            market_portfolio_backtest_evaluator_bridge=None,
            market_portfolio_backtester=None,
            market_portfolio_collector_agent=None,
            market_portfolio_data_exporter=None,
            market_portfolio_digest=None,
            market_portfolio_dividend_tracker=None,
            market_portfolio_event_intelligence_hub=None,
            market_portfolio_execution_cost_optimizer=None,
            market_portfolio_execution_pipeline=None,
            market_portfolio_integration_hub=None,
            market_portfolio_monitor=None,
            market_portfolio_performance_analytics=None,
            market_portfolio_predictive_aggregator=None,
            market_portfolio_scenario_simulator=None,
            market_portfolio_slippage_model=None,
            market_portfolio_strategy_optimizer=None,
            market_portfolio_stress_audit_visualizer=None,
            market_portfolio_stress_monte_carlo_engine=None,
            market_portfolio_stress_recovery_coordinator_bridge=None,
            market_portfolio_stress_reporter=None,
            market_portfolio_stress_scenario_pipeline=None,
            market_portfolio_tax_calculator=None,
            market_portfolio_telegram_command_center=None,
            market_portfolio_telegram_notifier=None,
            market_portfolio_valuation=None,
            market_portfolio_var_liquidity_core=self.mock_core,
            market_portfolio_visualizer_v2=None,
            market_portfolio_webhook_event_logger=None,
            market_portfolio_webhook_sync=None,
            market_report_generator=None,
            market_sentiment_digest=None,
            market_sentiment_risk_alert_bridge=None,
            market_sentiment_risk_hub=None,
            market_sentiment_telegram_publisher=None,
            market_telegram_pipeline=None
        )

    def test_aggregate_success(self):
        rand_id = uuid.uuid4().hex
        extracted_val = uuid.uuid4().hex
        core_val = random.uniform(0, 1000)

        self.mock_extractor.extract.return_value = extracted_val
        self.mock_core.compute.return_value = core_val

        result = self.aggregator.aggregate(rand_id)

        self.assertEqual(result["extracted"], extracted_val)
        self.assertEqual(result["core_liquidity"], core_val)
        self.mock_db.save.assert_called_once_with(rand_id, result)

    def test_aggregate_exception_handling(self):
        rand_id = uuid.uuid4().hex
        error_msg = uuid.uuid4().hex
        self.mock_extractor.extract.side_effect = Exception(error_msg)

        with self.assertRaises(Exception):
            self.aggregator.aggregate(rand_id)

        self.mock_notifier.notify.assert_called_once_with(error_msg)

    def test_aggregate_macro_liquidity_file_persistence(self):
        portfolio_id = uuid.uuid4().hex
        context = {"data": uuid.uuid4().hex}
        liquidity_data = {"val": random.random()}
        export_path = f"{uuid.uuid4().hex}.json"

        try:
            result = self.aggregator.aggregate_macro_liquidity(portfolio_id, context, liquidity_data, export_path)

            self.assertTrue(os.path.exists(export_path))
            with open(export_path, 'r') as f:
                saved_data = json.load(f)
                self.assertEqual(saved_data["portfolio_id"], portfolio_id)
        finally:
            if os.path.exists(export_path):
                os.remove(export_path)

    def test_parse_external_stream_content(self):
        url = f"https://{uuid.uuid4().hex}.com"
        content_id = uuid.uuid4().hex
        random_content = f"<html><body>{content_id}</body></html>".encode('utf-8')

        with patch('requests.get') as mock_get:
            mock_get.return_value.content = random_content
            soup = self.aggregator.parse_external_stream(url)
            self.assertIn(content_id[:5], soup.text) # Проверка наличия контента

if __name__ == '__main__':
    unittest.main()