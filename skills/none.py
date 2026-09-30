import io
import os
import json
import uuid
import requests

from skills.market_parser import market_parser, MarketParser
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_strategy_optimizer import market_portfolio_strategy_optimizer
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.market_report_generator import market_report_generator
from skills.db_storage import db_storage

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
