import os
import requests
from skills.db_storage import (
    save_macro_liquidity_state,
    get_macro_liquidity_state,
    save_macro_metric
)
from skills.market_parser import fetch_macro_indicators
from skills.market_portfolio_var_liquidity_core import calculate_var_liquidity
from skills.market_portfolio_stress_scenario_pipeline import run_stress_scenario

def start_new(**kwargs):
    db_storage = kwargs.get("db_storage")
    market_parser = kwargs.get("market_parser")
    anomaly_detector = kwargs.get("market_anomaly_detector")
    portfolio_dispatcher = kwargs.get("market_portfolio_alert_dispatcher")

    macro_data = {}
    if market_parser and hasattr(market_parser, "fetch_macro_data"):
        macro_data = market_parser.fetch_macro_data() or {}
        token = macro_data.get("token") if isinstance(macro_data, dict) else None
        if token and isinstance(token, str):
            url = f"http://localhost/macro/{token}"
            try:
                resp = requests.get(url, timeout=5)
                if resp and resp.status_code == 200:
                    pass
            except Exception:
                pass

    if db_storage and hasattr(db_storage, "save_macro_metric"):
        db_storage.save_macro_metric(macro_data)

    if anomaly_detector and hasattr(anomaly_detector, "detect"):
        anomaly_res = anomaly_detector.detect()
        if anomaly_res and anomaly_res.get("anomaly"):
            if portfolio_dispatcher and hasattr(portfolio_dispatcher, "dispatch"):
                portfolio_dispatcher.dispatch(anomaly_res)

    return {"status": "success", "data": macro_data}

def monitor_macro_liquidity(market_data: dict, threshold_factor: float) -> dict:
    run_id = market_data.get("run_id") if market_data else None
    interest_rate = market_data.get("interest_rate", 0.05) if market_data else 0.05

    liquidity_score = max(0.0, round(1.0 - (interest_rate * threshold_factor), 4))
    risk_multiplier = round(1.0 + (interest_rate * threshold_factor), 4)

    return {
        "run_id": run_id,
        "liquidity_score": liquidity_score,
        "risk_multiplier": risk_multiplier,
        "logged": True
    }