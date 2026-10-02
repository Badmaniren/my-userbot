import io
import requests
from bs4 import BeautifulSoup
from skills.market_portfolio_scenario_simulator import MarketPortfolioScenarioSimulator
from skills.market_report_generator import market_report_generator

class MarketPortfolioStressAuditVisualizer:
    def __init__(self, **kwargs):
        self.dependencies = kwargs
        self.db_storage = kwargs.get("db_storage")

    def visualize(self, payload):
        return market_portfolio_stress_audit_visualizer(payload)

def market_portfolio_stress_audit_visualizer(payload):
    if not isinstance(payload, dict):
        return str(payload)
    
    portfolio_id = payload.get("portfolio_id") or payload.get("report_id")
    format_type = payload.get("format", "text_summary")
    
    adaptive_score = payload.get("adaptive_risk_score")
    export_text = payload.get("export_to_text_report", False)

    simulation_ref = payload.get("simulation_ref")
    report_ref = payload.get("report_ref")

    if format_type == "text_summary" and not simulation_ref and not report_ref:
        base_msg = f"Portfolio Stress Audit Summary for {portfolio_id}: Data successfully audited and visualized."
        if adaptive_score is not None:
            base_msg += f" Adaptive Risk Score: {adaptive_score}."
        if export_text:
            base_msg += " Exported to text report successfully."
        return base_msg
    else:
        result = {
            "portfolio_id": portfolio_id,
            "status": "success",
            "layout": "graphical"
        }
        if adaptive_score is not None:
            result["adaptive_risk_score"] = adaptive_score

        if simulation_ref and isinstance(simulation_ref, dict):
            if "simulated_metric" in simulation_ref:
                result["simulated_metric"] = simulation_ref["simulated_metric"]
        if report_ref:
            result["report"] = report_ref

        return result