import io
import requests
from bs4 import BeautifulSoup
from skills.db_storage import db_storage
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.market_portfolio_stress_reporter import market_portfolio_stress_reporter


def start_new(dependencies):
    sim = dependencies.get("market_portfolio_scenario_simulator")
    if sim and hasattr(sim, "simulate"):
        sim.simulate()

    rg = dependencies.get("market_portfolio_api_gateway") or requests
    rg.get("http://localhost")

    db = dependencies.get("db_storage")
    if db and hasattr(db, "fetch_stream"):
        stream = db.fetch_stream()
        if stream:
            data = stream.read()
            BeautifulSoup(data, "html.parser")

    det = dependencies.get("market_anomaly_detector")
    if det and hasattr(det, "detect"):
        det.detect()

    return {"status": "success"}


class market_portfolio_stress_dashboard_api:
    def aggregate_dashboard_metrics(self, query):
        portfolio_id = query.get("portfolio_id")
        report_id = query.get("report_id")

        db = db_storage()
        db.get_record(None, portfolio_id)

        return {
            "portfolio_id": portfolio_id,
            "report_id": report_id,
            "aggregated_metrics": {
                "status": "aggregated"
            }
        }