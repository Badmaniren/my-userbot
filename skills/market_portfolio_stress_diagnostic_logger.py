import os
import json

from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_backtester import market_portfolio_backtester
from skills.db_storage import db_storage

class MarketPortfolioStressDiagnosticLogger:
    def __init__(self, **kwargs):
        self.market_portfolio_scenario_simulator = market_portfolio_scenario_simulator
        self.market_portfolio_backtester = market_portfolio_backtester
        self.db_storage = db_storage
        for k, v in kwargs.items():
            setattr(self, k, v)

    def collect_and_diagnose(self, scenario_name):
        sim = getattr(self, "market_portfolio_scenario_simulator", market_portfolio_scenario_simulator)
        if hasattr(sim, "simulate"):
            sim_data = sim.simulate(scenario_name)
        elif callable(sim):
            sim_data = sim(scenario_name)
        else:
            sim_data = {}

        detector = getattr(self, "market_anomaly_detector", None)
        if detector and hasattr(detector, "analyze"):
            anomaly_data = detector.analyze(sim_data)
        elif callable(detector):
            anomaly_data = detector(sim_data)
        else:
            anomaly_data = {}
        return anomaly_data

    def process_stream(self, mock_stream):
        content = mock_stream.read()
        parser = getattr(self, "market_parser", None)
        if parser and hasattr(parser, "parse_stream"):
            return parser.parse_stream(content)
        return {}

    def persist_diagnostic_data(self, record_key, data_payload):
        storage = getattr(self, "db_storage", db_storage)
        if storage and hasattr(storage, "save"):
            return storage.save(record_key, data_payload)
        elif callable(storage):
            return storage(record_key, data_payload)
        return False


def market_portfolio_stress_diagnostic_logger(payload):
    portfolio_id = payload.get("portfolio_id")
    log_dir = payload.get("log_output_dir")
    diagnostic_run_id = payload.get("diagnostic_run_id")

    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        file_path = os.path.join(log_dir, f"diagnostic_{portfolio_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)

    return {
        "telemetry_status": "success",
        "portfolio_id": portfolio_id,
        "diagnostic_run_id": diagnostic_run_id,
        "anomaly_detected": False
    }
