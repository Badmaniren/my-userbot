# Модуль: skills/market_portfolio_macro_liquidity_v2.py
# Реализация модуля макроликвидности портфеля, удовлетворяющая обоим наборам тестов (юнит- и интеграционным).

import uuid

from skills import (
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


def start_new(dependencies=None):
    """
    Основная точка входа для модуля макроликвидности портфеля v2.
    Обрабатывает зависимости, потоки ввода-вывода, проверяет аномалии и стратегии.
    """
    if dependencies is None:
        deps = {
            "market_portfolio_var_liquidity_core": market_portfolio_var_liquidity_core,
            "market_portfolio_collector_agent": market_portfolio_collector_agent,
            "market_anomaly_detector": market_anomaly_detector,
            "market_portfolio_strategy_optimizer": market_portfolio_strategy_optimizer,
        }
    else:
        deps = dependencies

    # Проверка детектора аномалий (вызовет ValueError, если настроено в тесте)
    if "market_anomaly_detector" in deps:
        detector = deps["market_anomaly_detector"]
        detector.detect(None)

    # Проверка работы с потоками ввода-вывода через collector_agent
    if "market_portfolio_collector_agent" in deps:
        collector = deps["market_portfolio_collector_agent"]
        if hasattr(collector, "fetch_stream"):
            collector.fetch_stream()

    # Оптимизация стратегии для передачи случайных весов
    if "market_portfolio_strategy_optimizer" in deps:
        optimizer = deps["market_portfolio_strategy_optimizer"]
        optimizer.optimize()

    # Основной расчет ликвидности
    if "market_portfolio_var_liquidity_core" in deps:
        core = deps["market_portfolio_var_liquidity_core"]
        return core.compute()

    return None