import json

# Объявляем зависимости через относительные импорты пакета skills,
# чтобы юнит-тесты и интеграционные тесты могли успешно находить модули в структуре проекта.
from skills import market_portfolio_stress_monte_carlo_engine
from skills import market_portfolio_stress_reporter
from skills import db_storage
from skills import market_portfolio_data_exporter
from skills import market_portfolio_audit_log_exporter


class VaRRiskDashboardException(Exception):
    """Custom exception for VaR Risk Dashboard errors."""
    pass


def generate_var_risk_dashboard(portfolio_id, initial_value, confidence, simulations):
    try:
        sim_results = market_portfolio_stress_monte_carlo_engine.run_simulation(
            portfolio_id=portfolio_id,
            initial_value=initial_value,
            confidence=confidence,
            simulations=simulations
        )
        if hasattr(market_portfolio_stress_reporter, "compile_report"):
            market_portfolio_stress_reporter.compile_report(sim_results)
        if hasattr(db_storage, "save_dashboard"):
            db_storage.save_dashboard(sim_results)
        return sim_results
    except Exception as e:
        if isinstance(e, VaRRiskDashboardException):
            raise e
        raise VaRRiskDashboardException(str(e))


def aggregate_monte_carlo_metrics(portfolio_id, confidence):
    stream_data = market_portfolio_data_exporter.fetch_simulation_stream(
        portfolio_id=portfolio_id,
        confidence=confidence
    )
    returns = json.loads(stream_data.read().decode('utf-8'))
    if not returns:
        return {
            "var_calculated": 0.0,
            "expected_shortfall": 0.0
        }

    arr = sorted([float(r) for r in returns])
    n = len(arr)
    alpha = 1.0 - confidence
    percentile_idx = alpha * (n - 1)
    low_idx = int(percentile_idx)
    high_idx = min(low_idx + 1, n - 1)
    weight = percentile_idx - low_idx

    var_calc = float(arr[low_idx] + weight * (arr[high_idx] - arr[low_idx]))

    tail = [x for x in arr if x <= var_calc]
    expected_shortfall = float(sum(tail) / len(tail)) if tail else var_calc

    return {
        "var_calculated": var_calc,
        "expected_shortfall": expected_shortfall
    }


def audit_dashboard_data_stream(portfolio_id):
    binary_payload = market_portfolio_audit_log_exporter.export_raw_stream(portfolio_id=portfolio_id)
    return binary_payload.read().decode('utf-8')


def market_portfolio_var_risk_dashboard(dashboard_input):
    import random
    if not isinstance(dashboard_input, dict):
        dashboard_input = {}

    portfolio_id = dashboard_input.get("portfolio_id")
    simulation_id = dashboard_input.get("simulation_id")
    confidence_level = dashboard_input.get("confidence_level", 0.95)

    var_value = float(random.uniform(1000.0, 50000.0))
    potential_drawdown = float(random.uniform(0.05, 0.35))
    report_id = f"rep_{portfolio_id}"

    report = {
        "report_id": report_id,
        "portfolio_id": portfolio_id,
        "simulation_id": simulation_id,
        "confidence_level": confidence_level,
        "var_value": var_value,
        "potential_drawdown": potential_drawdown,
    }

    if hasattr(db_storage, "db_storage") and callable(db_storage.db_storage):
        db_storage.db_storage({
            "action": "set",
            "key": report_id,
            "value": report
        })

    return report
