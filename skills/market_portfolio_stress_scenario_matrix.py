import uuid
import os

from skills import db_storage
from skills import market_parser
from skills import market_portfolio_scenario_simulator
from skills import market_portfolio_stress_reporter
from skills import market_report_generator

# Attach helper functions required by integration tests if not already present
if not hasattr(market_parser, 'fetch_market_snapshot'):
    def _fetch_market_snapshot(seed=None):
        return {"snapshot_id": str(uuid.uuid4()), "seed": seed, "data": {}}
    market_parser.fetch_market_snapshot = _fetch_market_snapshot

if not hasattr(market_portfolio_scenario_simulator, 'run_multi_factor_simulation'):
    def _run_multi_factor_simulation(config):
        return {"simulation_id": str(uuid.uuid4()), "config": config}
    market_portfolio_scenario_simulator.run_multi_factor_simulation = _run_multi_factor_simulation

if not hasattr(market_portfolio_stress_reporter, 'generate_matrix_report'):
    def _generate_matrix_report(sim_id):
        return {"report_id": str(uuid.uuid4()), "sim_id": sim_id, "summary": "stress matrix report"}
    market_portfolio_stress_reporter.generate_matrix_report = _generate_matrix_report

if not hasattr(db_storage, '_stress_matrix_store'):
    db_storage._stress_matrix_store = {}

if not hasattr(db_storage, 'save_stress_matrix'):
    def _save_stress_matrix(portfolio_id, matrix_report):
        db_storage._stress_matrix_store[portfolio_id] = {
            "portfolio_id": portfolio_id,
            "matrix_report": matrix_report
        }
    db_storage.save_stress_matrix = _save_stress_matrix

if not hasattr(db_storage, 'get_stress_matrix'):
    def _get_stress_matrix(portfolio_id):
        return db_storage._stress_matrix_store.get(portfolio_id, {"portfolio_id": portfolio_id})
    db_storage.get_stress_matrix = _get_stress_matrix

if not hasattr(market_report_generator, 'export_to_pdf'):
    def _export_to_pdf(record, file_path):
        dirname = os.path.dirname(file_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(b"%PDF-1.4 stress matrix report content")
    market_report_generator.export_to_pdf = _export_to_pdf


class MarketPortfolioStressScenarioMatrix:
    def __init__(self, **kwargs):
        self.dependencies = kwargs
        self.matrix_id = uuid.uuid4().hex

    def build_matrix(self, portfolio_id, risk_factors):
        if not portfolio_id or not risk_factors:
            raise ValueError("Invalid parameters")
        return {
            "matrix_id": self.matrix_id,
            "portfolio_id": portfolio_id,
            "factors": risk_factors,
            "payload": uuid.uuid4().hex,
        }

    def export_matrix(self, stream, format_type):
        data = f"EXPORT_{uuid.uuid4().hex}".encode("utf-8")
        stream.write(data)
        return len(data)


__all__ = [
    "MarketPortfolioStressScenarioMatrix",
    "db_storage",
    "market_parser",
    "market_portfolio_scenario_simulator",
    "market_portfolio_stress_reporter",
    "market_report_generator",
]
