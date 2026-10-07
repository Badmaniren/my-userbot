import io
import os
import random
import string
import uuid

from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_stress_scenario_pipeline import (
    market_portfolio_stress_scenario_pipeline,
)


class MarketPortfolioStressDiagnosticReportExporter:
    def __init__(self, **kwargs):
        self.db_storage = kwargs.get('db_storage')
        self.market_portfolio_scenario_simulator = kwargs.get('market_portfolio_scenario_simulator')
        self.market_portfolio_stress_reporter = kwargs.get('market_portfolio_stress_reporter')
        self.market_portfolio_stress_monte_carlo_engine = kwargs.get('market_portfolio_stress_monte_carlo_engine')
        self.market_portfolio_alert_dispatcher = kwargs.get('market_portfolio_alert_dispatcher')

    def export_report(self, portfolio_id, scenario_id):
        self.market_portfolio_scenario_simulator.simulate(portfolio_id, scenario_id)
        return self.market_portfolio_stress_reporter.generate_report()

    def export_to_stream(self, portfolio_id, scenario_id):
        return self.market_portfolio_stress_reporter.generate_stream(portfolio_id, scenario_id)

    def fetch_diagnostic_data(self, portfolio_id):
        return self.db_storage.fetch_diagnostic_data(portfolio_id)

    def check_and_dispatch_stress_alerts(self, portfolio_id):
        risk = self.market_portfolio_stress_monte_carlo_engine.evaluate_risk(portfolio_id)
        if risk.get("critical"):
            self.market_portfolio_alert_dispatcher.dispatch(risk.get("message"))


def market_portfolio_stress_diagnostic_report_exporter(exporter_input):
    scenario_id = exporter_input.get("scenario_id")
    portfolio_id = exporter_input.get("portfolio_id")
    output_path = exporter_input.get("output_path")

    with open(output_path, "wb") as f:
        f.write(b"PDF diagnostic report content")

    return {
        "status": "success",
        "scenario_id": scenario_id,
        "portfolio_id": portfolio_id
    }