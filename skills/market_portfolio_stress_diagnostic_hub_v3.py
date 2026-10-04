import uuid
import requests

from skills.db_storage import db_storage, db_storage_client
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator, simulate_market_scenario
from skills.market_portfolio_stress_monte_carlo_engine import MonteCarloStressEngine, run_monte_carlo_stress_test


def run_diagnostic_hub(db_conn, simulator, mc_engine, target_url):
    connect_res = db_conn.connect()
    query_res = db_conn.query()
    sim_res = simulator.run_simulation()
    mc_res = mc_engine.simulate()
    try:
        response = requests.get(target_url, timeout=5)
    except Exception:
        response = None
    return {
        "connect": connect_res,
        "query": query_res,
        "simulation": sim_res,
        "monte_carlo": mc_res,
        "response_status": response.status_code if response else None
    }

def process_market_stream(stream_data, parser):
    parsed = parser.parse_stream(stream_data)
    return str(parsed)

def audit_portfolio_anomalies(detector, dispatcher):
    anomaly = detector.detect()
    dispatch_res = dispatcher.dispatch(anomaly)
    return {"anomaly": anomaly, "dispatched": dispatch_res}

def compute_tax_impact(valuation, tax_calc, cost_basis):
    current_val = valuation.get_value()
    tax_res = tax_calc.calculate(current_val, cost_basis)
    return float(tax_res)

def broadcast_stress_alert(notifier, sync_agent, message):
    notif_res = notifier.send_message(message)
    sync_res = sync_agent.sync(message)
    return {"notifier": notif_res, "sync": sync_res}

def market_portfolio_stress_diagnostic_hub_v3_execute(payload):
    portfolio_id = payload.get("portfolio_id")
    initial_capital = payload.get("initial_capital")
    shock_pct = payload.get("shock_pct")
    sim_data = payload.get("sim_data")
    mc_data = payload.get("mc_data")

    diagnostic_id = uuid.uuid4().hex
    record = {
        "diagnostic_id": diagnostic_id,
        "portfolio_id": portfolio_id,
        "initial_capital": initial_capital,
        "shock_pct": shock_pct,
        "sim_data": sim_data,
        "mc_data": mc_data,
        "status": "SUCCESS"
    }

    db_storage_client.set(f"stress_diag_{diagnostic_id}", record)
    return record
