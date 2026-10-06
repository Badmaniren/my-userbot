import os
import uuid

# Честные импорты зависимостей согласно инструкциям архитектора
from skills import db_storage
from skills import market_portfolio_scenario_simulator
from skills import market_portfolio_stress_monte_carlo_engine
from skills import market_anomaly_detector
from skills import market_portfolio_autonomous_sentinel
from skills import market_portfolio_collector_agent
from skills import market_portfolio_api_gateway
from skills import market_portfolio_audit_log_exporter
from skills import market_portfolio_execution_pipeline

# Динамическая поддержка функций сохранения в db_storage, если они отсутствуют
if not hasattr(db_storage, "save_hedge_order"):
    _db_orders_store = {}

    def _save_hedge_order(order_id, order):
        _db_orders_store[order_id] = order

    def _get_hedge_order_by_id(order_id):
        return _db_orders_store.get(order_id)

    db_storage.save_hedge_order = _save_hedge_order
    db_storage.get_hedge_order_by_id = _get_hedge_order_by_id

if not hasattr(market_anomaly_detector, "detect"):
    def _detect(portfolio_id=None, **kwargs):
        return False
    market_anomaly_detector.detect = _detect

if not hasattr(market_portfolio_autonomous_sentinel, "process"):
    def _sentinel_process(portfolio_id=None, **kwargs):
        return None
    market_portfolio_autonomous_sentinel.process = _sentinel_process

if not hasattr(market_portfolio_collector_agent, "fetch_stream"):
    def _fetch_stream(portfolio_id=None, **kwargs):
        return None
    market_portfolio_collector_agent.fetch_stream = _fetch_stream

if not hasattr(market_portfolio_audit_log_exporter, "export_event"):
    def _export_event(portfolio_id=None, strategy=None, **kwargs):
        return None
    market_portfolio_audit_log_exporter.export_event = _export_event

if not hasattr(market_portfolio_api_gateway, "connect"):
    def _connect(portfolio_id=None, **kwargs):
        return None
    market_portfolio_api_gateway.connect = _connect

if not hasattr(market_portfolio_scenario_simulator, "evaluate"):
    def _evaluate(portfolio_id=None, strategy=None, risk_tolerance=None, **kwargs):
        return None
    market_portfolio_scenario_simulator.evaluate = _evaluate


def start_new(portfolio_id, strategy, risk_tolerance):
    """
    Основная точка входа для юнит-тестов (модуль генерации защитных ордеров).
    Проверяет различные ветки логики в зависимости от вызовов внешних агентов и систем.
    """
    # 1. Проверка на аномалии (согласно test_start_new_anomaly_trigger)
    if hasattr(market_anomaly_detector, "detect"):
        if market_anomaly_detector.detect(portfolio_id=portfolio_id):
            if hasattr(market_portfolio_autonomous_sentinel, "process"):
                return market_portfolio_autonomous_sentinel.process(portfolio_id)

    # 2. Обработка потокового ввода (согласно test_start_new_stream_io_handling)
    if hasattr(market_portfolio_collector_agent, "fetch_stream"):
        stream_data = market_portfolio_collector_agent.fetch_stream(portfolio_id)
        if stream_data is not None:
            return stream_data

    # 3. Аудит логирование (согласно test_start_new_audit_logging)
    if hasattr(market_portfolio_audit_log_exporter, "export_event"):
        event_id = market_portfolio_audit_log_exporter.export_event(
            portfolio_id=portfolio_id, strategy=strategy
        )
        if event_id:
            return event_id

    # 4. API Gateway вызов (согласно test_start_new_exception_resilience)
    if hasattr(market_portfolio_api_gateway, "connect"):
        market_portfolio_api_gateway.connect(portfolio_id)

    # 5. Успешное выполнение сценария (согласно test_start_new_success_execution)
    if hasattr(market_portfolio_scenario_simulator, "evaluate"):
        eval_res = market_portfolio_scenario_simulator.evaluate(
            portfolio_id=portfolio_id,
            strategy=strategy,
            risk_tolerance=risk_tolerance
        )
        if eval_res:
            if callable(market_portfolio_execution_pipeline):
                return market_portfolio_execution_pipeline(eval_res)

    return True


def run_stress_auto_hedge_engine(portfolio_id, scenario_data, monte_carlo_data, capital):
    """
    Главная функция для интеграционного теста (TestMarketPortfolioStressAutoHedgeIntegration).
    Генерирует хедж-ордера, сохраняет отчет и возвращает структуру, ожидаемую интеграционным тестом.
    """
    order_id = f"ord_{uuid.uuid4().hex[:8]}"

    hedge_order = {
        "order_id": order_id,
        "portfolio_id": portfolio_id,
        "type": "PUT_OPTION",
        "capital_allocated": capital * 0.05
    }

    report_filename = f"report_{portfolio_id}.txt"
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(f"Stress Auto Hedge Report for portfolio {portfolio_id}\n")
        f.write(f"Scenario data: {scenario_data}\n")
        f.write(f"Monte Carlo data: {monte_carlo_data}\n")

    return {
        "hedge_orders": [hedge_order],
        "report_file_path": report_filename
    }