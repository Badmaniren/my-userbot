import unittest
import uuid
import random
import os

from skills.market_macro_liquidity_dashboard_pipeline import (
    db_storage,
    extractor_tool_1790087207,
    extractor_tool_1790102839,
    extractor_tool_1790262909,
    extractor_tool_1790621808,
    market_anomaly_detector,
    market_insider_activity_tracker,
    market_insider_alert_pipeline,
    market_insider_anomaly_analyzer,
    market_insider_anomaly_report_bridge,
    market_news_sentiment_analyzer,
    market_parser,
    market_portfolio_alert_dispatcher,
    market_portfolio_alert_event_sink,
    market_portfolio_alert_filter_router,
    market_portfolio_api_gateway,
    market_portfolio_audit_alert_notifier,
    market_portfolio_audit_compliance_hub,
    market_portfolio_audit_log_exporter,
    market_portfolio_autonomous_sentinel,
    market_portfolio_backtest_evaluator_bridge,
    market_portfolio_backtester,
    market_portfolio_collector_agent,
    market_portfolio_data_exporter,
    market_portfolio_digest,
    market_portfolio_dividend_tracker,
    market_portfolio_event_intelligence_hub,
    market_portfolio_execution_cost_optimizer,
    market_portfolio_execution_pipeline,
    market_portfolio_integration_hub,
    market_portfolio_liquidity_scenario_analyzer,
    market_portfolio_monitor,
    market_portfolio_performance_analytics,
    market_portfolio_predictive_aggregator,
    market_portfolio_scenario_simulator,
    market_portfolio_slippage_model,
    market_portfolio_strategy_optimizer,
    market_portfolio_stress_audit_visualizer,
    market_portfolio_stress_monte_carlo_engine,
    market_portfolio_stress_recovery_coordinator_bridge,
    market_portfolio_stress_reporter,
    market_portfolio_stress_scenario_pipeline,
    market_portfolio_tax_calculator,
    market_portfolio_telegram_command_center,
    market_portfolio_telegram_notifier,
    market_portfolio_valuation,
    market_portfolio_var_liquidity_core,
    market_portfolio_visualizer_v2,
    market_portfolio_webhook_event_logger,
    market_portfolio_webhook_sync,
    market_report_generator,
    market_sentiment_digest,
    market_sentiment_risk_alert_bridge,
    market_sentiment_risk_hub,
    market_sentiment_telegram_publisher,
    market_telegram_pipeline
)

class TestMarketMacroLiquidityDashboardPipelineIntegration(unittest.TestCase):

    def test_macro_liquidity_pipeline_flow(self):
        run_id = str(uuid.uuid4())
        portfolio_id = str(uuid.uuid4())
        macro_metric_val = round(random.uniform(100.0, 1000.0), 2)
        liquidity_score = round(random.uniform(0.1, 0.99), 4)

        # 1. Сбор данных через экстракторы и коллекторы
        extracted_data_1 = extractor_tool_1790087207({"run_id": run_id, "mode": "macro"})
        extracted_data_2 = extractor_tool_1790102839({"portfolio_id": portfolio_id})
        extracted_data_3 = extractor_tool_1790262909({"metric": macro_metric_val})
        extracted_data_4 = extractor_tool_1790621808({"liquidity": liquidity_score})

        collector_result = market_portfolio_collector_agent.collect({
            "run_id": run_id,
            "portfolio_id": portfolio_id,
            "raw": [extracted_data_1, extracted_data_2, extracted_data_3, extracted_data_4]
        })
        self.assertIsNotNone(collector_result)

        # 2. Анализ аномалий и ликвидности
        anomaly_check = market_anomaly_detector.detect({"run_id": run_id, "threshold": random.uniform(1.0, 5.0)})
        liquidity_core_res = market_portfolio_var_liquidity_core.evaluate({
            "portfolio_id": portfolio_id,
            "score": liquidity_score
        })
        self.assertIsNotNone(anomaly_check)
        self.assertIsNotNone(liquidity_core_res)

        # 3. Сохранение в реальную базу данных
        db_storage.save_pipeline_state({
            "run_id": run_id,
            "portfolio_id": portfolio_id,
            "macro_metric": macro_metric_val,
            "liquidity": liquidity_score
        })

        stored_record = db_storage.get_pipeline_state(run_id)
        self.assertIsNotNone(stored_record)
        self.assertEqual(stored_record.get("portfolio_id"), portfolio_id)

        # 4. Генерация отчета и дашборда
        report_path = f"report_{run_id}.json"
        market_report_generator.generate({
            "run_id": run_id,
            "data": stored_record,
            "output": report_path
        })

        self.assertTrue(os.path.exists(report_path), "Интеграционный пайплайн должен создавать реальный файл отчета.")

        # Очистка за собой
        if os.path.exists(report_path):
            os.remove(report_path)


if __name__ == "__main__":
    unittest.main()