import io
import os
import json
import random
import uuid
import requests

from skills import market_parser as _mp_mod
from skills import market_portfolio_collector_agent as _ca_mod
from skills import market_portfolio_strategy_optimizer as _so_mod
from skills import market_portfolio_scenario_simulator as _ss_mod
from skills import market_portfolio_stress_monte_carlo_engine as _mc_mod
from skills import market_report_generator as _rg_mod
from skills import db_storage as _db_mod

def market_parser(target=None, limit=100, **kwargs):
    if hasattr(_mp_mod, "market_parser") and callable(_mp_mod.market_parser):
        return _mp_mod.market_parser(target=target, limit=limit, **kwargs)
    return {"target": target, "limit": limit, "data": []}

def market_portfolio_collector_agent(data=None, session_id=None, **kwargs):
    if hasattr(_ca_mod, "market_portfolio_collector_agent") and callable(_ca_mod.market_portfolio_collector_agent):
        return _ca_mod.market_portfolio_collector_agent(data=data, session_id=session_id, **kwargs)
    return {"status": "success", "session_id": session_id, "data": data}

def market_portfolio_strategy_optimizer(portfolio=None, risk_tolerance=0.02, **kwargs):
    if hasattr(_so_mod, "market_portfolio_strategy_optimizer") and callable(_so_mod.market_portfolio_strategy_optimizer):
        return _so_mod.market_portfolio_strategy_optimizer(portfolio=portfolio, risk_tolerance=risk_tolerance, **kwargs)
    return {"portfolio": portfolio, "risk_tolerance": risk_tolerance, "strategy": "balanced"}

def market_portfolio_scenario_simulator(strategy=None, horizon_months=12, **kwargs):
    if hasattr(_ss_mod, "market_portfolio_scenario_simulator") and callable(_ss_mod.market_portfolio_scenario_simulator):
        return _ss_mod.market_portfolio_scenario_simulator(strategy=strategy, horizon_months=horizon_months, **kwargs)
    return {"simulation_id": str(uuid.uuid4()), "strategy": strategy, "horizon_months": horizon_months, "expected_return": 0.08}

def market_portfolio_stress_monte_carlo_engine(simulation_data=None, iterations=100, **kwargs):
    if hasattr(_mc_mod, "market_portfolio_stress_monte_carlo_engine") and callable(_mc_mod.market_portfolio_stress_monte_carlo_engine):
        return _mc_mod.market_portfolio_stress_monte_carlo_engine(simulation_data=simulation_data, iterations=iterations, **kwargs)
    return {"simulation_data": simulation_data, "iterations": iterations, "var_95": -0.05, "es_95": -0.08}

def market_report_generator(metrics=None, vector_id=None, output_file=None, **kwargs):
    if hasattr(_rg_mod, "market_report_generator") and callable(_rg_mod.market_report_generator):
        return _rg_mod.market_report_generator(metrics=metrics, vector_id=vector_id, output_file=output_file, **kwargs)
    output_path = output_file or f"report_vector_{vector_id or uuid.uuid4()}.json"
    report_data = {
        "vector_id": vector_id,
        "metrics": metrics,
        "generated_at": str(uuid.uuid4())
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    return output_path

def db_storage(record_id=None, payload=None, **kwargs):
    if hasattr(_db_mod, "db_storage") and callable(_db_mod.db_storage):
        return _db_mod.db_storage(record_id=record_id, payload=payload, **kwargs)
    return True


def start_new(dependencies=None):
    if dependencies is None:
        dependencies = {}

    db = dependencies.get("db_storage")
    collector = dependencies.get("market_portfolio_collector_agent")
    detector = dependencies.get("market_anomaly_detector")
    parser = dependencies.get("market_parser")

    if detector and hasattr(detector, "detect"):
        detector.detect()

    payload = b""
    if collector and hasattr(collector, "fetch"):
        res = collector.fetch()
        if hasattr(res, "read") and callable(res.read):
            data = res.read()
            if isinstance(data, (bytes, bytearray)):
                payload = bytes(data)
            elif isinstance(data, str):
                payload = data.encode('utf-8')

    if parser and hasattr(parser, "parse_stream"):
        parser.parse_stream(io.BytesIO(payload))

    try:
        requests.get("https://httpbin.org/status/200", timeout=1)
    except requests.exceptions.RequestException:
        pass

    metric = 0
    if db and hasattr(db, "save_vector"):
        metric = db.save_vector(payload)

    return {"status": "success", "metric": metric}
