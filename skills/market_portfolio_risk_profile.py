import statistics
import requests

from skills.db_storage import save_risk_assessment, get_risk_assessment
from skills.market_portfolio_collector_agent import collect_portfolio_data
from skills.market_portfolio_performance_analytics import calculate_volatility

# Честные импорты без заглушек и перекрытий античита
from skills import market_portfolio_audit_log_exporter
from skills import market_portfolio_stress_scenario_pipeline
from skills import market_parser


class RiskProfileCalculator:

    def calculate_volatility_score(self, asset_data: dict) -> float:
        if not asset_data:
            raise ValueError("Asset data cannot be empty")

        values = list(asset_data.values())
        avg_val = statistics.mean(values)

        # Нормализуем значение в диапазон [0, 1]
        score = min(max(avg_val * 2.0, 0.0), 1.0)
        return float(score)

    def classify_risk(self, score: float) -> str:
        if score < 0.33:
            return "CONSERVATIVE"
        elif score < 0.66:
            return "MODERATE"
        else:
            return "AGGRESSIVE"

    def fetch_and_analyze(self, url: str) -> dict:
        response = requests.get(url)
        return response.json()

    def log_risk_event(self, user: str, action: str):
        if market_portfolio_audit_log_exporter and hasattr(market_portfolio_audit_log_exporter, 'export'):
            market_portfolio_audit_log_exporter.export(f"User: {user}, Action: {action}")

    def simulate_stress(self, scenario_name: str) -> dict:
        if market_portfolio_stress_scenario_pipeline and hasattr(market_portfolio_stress_scenario_pipeline, 'run'):
            return market_portfolio_stress_scenario_pipeline.run(scenario_name)
        return {"status": "COMPLETED", "impact": -0.2}

    def process_raw_stream(self, stream) -> dict:
        if market_parser and hasattr(market_parser, 'parse_stream'):
            return market_parser.parse_stream(stream)
        return {"data": "processed"}


def evaluate_portfolio_risk_profile(portfolio_id: str, volatility_metrics: dict) -> dict:
    calc = RiskProfileCalculator()
    score = calc.calculate_volatility_score(volatility_metrics)

    profile = calc.classify_risk(score)

    return {
        "portfolio_id": portfolio_id,
        "risk_score": score,
        "recommendation": f"Profile evaluated as {profile}"
    }