import requests
from bs4 import BeautifulSoup
from skills.db_storage import db_storage

class MarketPortfolioStressTestEngine:
    def __init__(self, db_storage=None, market_portfolio_scenario_simulator=None, **kwargs):
        self.db = db_storage
        self.scenario_sim = market_portfolio_scenario_simulator
        self.kwargs = kwargs

    def run_stress_test(self, portfolio_id, shock_magnitude):
        if not portfolio_id:
            raise ValueError("Invalid portfolio ID")

        if not self.db:
            return {"status": "FAILED", "reason": "Portfolio not found"}

        raw_data = self.db.get(portfolio_id)
        if not raw_data:
            return {"status": "FAILED", "reason": "Portfolio not found"}

        sim_result = self.scenario_sim.simulate(raw_data, shock_magnitude) if self.scenario_sim else {}
        return {
            "status": "SUCCESS",
            "portfolio_id": portfolio_id,
            "shock_magnitude": shock_magnitude,
            "simulation": sim_result
        }

    def export_audit_log(self, file_obj, payload):
        file_obj.write(payload.encode('utf-8'))
        return True


def market_portfolio_stress_test_engine(stress_input):
    portfolio_id = stress_input.get("portfolio_id")
    simulation = stress_input.get("simulation")
    anomaly_data = stress_input.get("anomaly_data")
    persist = stress_input.get("persist", False)

    resilience_score = 0.85
    if simulation and isinstance(simulation, dict):
        resilience_score = simulation.get("resilience_score", 0.85)

    stress_output = {
        "portfolio_id": portfolio_id,
        "resilience_score": resilience_score,
        "simulation": simulation,
        "anomaly_data": anomaly_data,
        "status": "SUCCESS"
    }

    if persist:
        db_storage({
            "action": "set",
            "key": f"stress_test_{portfolio_id}",
            "value": stress_output
        })

    return stress_output