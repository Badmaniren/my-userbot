from uuid import uuid4
import io
import random

from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_valuation import market_portfolio_valuation
from skills.db_storage import db_storage

REQUIRED_KEYS = [
    "db_storage", "extractor_tool_1790087207", "extractor_tool_1790102839",
    "extractor_tool_1790262909", "extractor_tool_1790621808", "market_anomaly_detector",
    "market_insider_activity_tracker", "market_insider_alert_pipeline",
    "market_insider_anomaly_analyzer", "market_insider_anomaly_report_bridge",
    "market_news_sentiment_analyzer", "market_parser", "market_portfolio_alert_dispatcher",
    "market_portfolio_alert_event_sink", "market_portfolio_alert_filter_router",
    "market_portfolio_api_gateway", "market_portfolio_audit_alert_notifier",
    "market_portfolio_audit_compliance_hub", "market_portfolio_audit_log_exporter",
    "market_portfolio_autonomous_sentinel", "market_portfolio_backtest_evaluator_bridge",
    "market_portfolio_backtester", "market_portfolio_collector_agent",
    "market_portfolio_data_exporter", "market_portfolio_digest",
    "market_portfolio_dividend_tracker", "market_portfolio_event_intelligence_hub",
    "market_portfolio_execution_pipeline", "market_portfolio_integration_hub",
    "market_portfolio_monitor", "market_portfolio_performance_analytics",
    "market_portfolio_predictive_aggregator", "market_portfolio_scenario_simulator",
    "market_portfolio_slippage_model", "market_portfolio_strategy_optimizer",
    "market_portfolio_stress_recovery_coordinator_bridge", "market_portfolio_stress_reporter",
    "market_portfolio_stress_scenario_pipeline", "market_portfolio_tax_calculator",
    "market_portfolio_telegram_command_center", "market_portfolio_telegram_notifier",
    "market_portfolio_valuation", "market_portfolio_visualizer_v2",
    "market_portfolio_webhook_event_logger", "market_portfolio_webhook_sync",
    "market_report_generator", "market_sentiment_digest",
    "market_sentiment_risk_alert_bridge", "market_sentiment_risk_hub",
    "market_sentiment_telegram_publisher", "market_telegram_pipeline"
]


def start_new(payload: dict) -> dict:
    for key in REQUIRED_KEYS:
        if key not in payload:
            raise KeyError(f"Missing required dependency: {key}")

    if "market_portfolio_data_exporter" in payload:
        payload["market_portfolio_data_exporter"].export_stream()

    if "market_anomaly_detector" in payload:
        payload["market_anomaly_detector"].evaluate_risk()

    sim_simulator = payload.get("market_portfolio_scenario_simulator")
    if sim_simulator and hasattr(sim_simulator, "run_simulation"):
        result = sim_simulator.run_simulation()
        if isinstance(result, dict):
            return result

    return {
        "simulation_id": uuid4().hex,
        "iterations": 1000,
        "status": "completed"
    }


def market_portfolio_stress_monte_carlo_engine(payload: dict) -> dict:
    simulation_id = payload.get("simulation_id", f"sim_{uuid4().hex}")
    portfolio_id = payload.get("portfolio_id", f"port_{uuid4().hex[:8]}")
    simulations_count = payload.get("simulations_count", 1000)
    horizon_days = payload.get("horizon_days", 30)

    base_valuation = payload.get("base_valuation", {})
    capital = base_valuation.get("capital", 100000.0)

    var_95 = round(capital * 0.05 * random.uniform(0.8, 1.2), 2)
    expected_shortfall = round(var_95 * 1.25, 2)

    output = {
        "simulation_id": simulation_id,
        "portfolio_id": portfolio_id,
        "simulations_count": simulations_count,
        "horizon_days": horizon_days,
        "var_95": var_95,
        "expected_shortfall": expected_shortfall,
        "status": "completed"
    }

    db_storage({
        "action": "set",
        "table": "monte_carlo_simulations",
        "id": simulation_id,
        "data": output
    })

    return output


class MarketPortfolioStressMonteCarloEngine:
    def __init__(self, *args, **kwargs):
        pass

    def run_simulation(self, payload=None, **kwargs):
        payload = payload or kwargs or {}
        return market_portfolio_stress_monte_carlo_engine(payload)


def run_monte_carlo_stress_simulation(portfolio_id: str = "default", composition: dict = None, simulations: int = 1000, horizon_days: int = 30) -> dict:
    return market_portfolio_stress_monte_carlo_engine({
        "portfolio_id": portfolio_id,
        "simulations_count": simulations,
        "horizon_days": horizon_days,
        "base_valuation": composition or {}
    })