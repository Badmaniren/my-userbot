import json
import statistics
from datetime import datetime
import io

from skills.market_portfolio_stress_monte_carlo_engine import run_monte_carlo_stress
from skills.market_portfolio_scenario_simulator import simulate_market_scenario
from skills.db_storage import save_trend_analysis_result, get_trend_analysis_result
from skills import market_portfolio_audit_log_exporter


class VaRTrendAnalyzer:
    def __init__(self, db_storage=None, market_portfolio_scenario_simulator=None, market_portfolio_stress_reporter=None):
        self.db_storage = db_storage
        self.market_portfolio_scenario_simulator = market_portfolio_scenario_simulator
        self.market_portfolio_stress_reporter = market_portfolio_stress_reporter

    def _fetch_historical_var(self, portfolio_id, timeframe_days):
        if self.db_storage and hasattr(self.db_storage, "get_historical_var"):
            return self.db_storage.get_historical_var(portfolio_id, timeframe_days)
        return []

    def analyze_trend(self, portfolio_id, timeframe_days):
        records = self._fetch_historical_var(portfolio_id, timeframe_days)
        if not records:
            return {
                "status": "insufficient_data",
                "data_points_analyzed": 0
            }

        var_values = [r["var_value"] for r in records]
        mean_val = statistics.mean(var_values)
        vol_val = statistics.pstdev(var_values) if len(var_values) > 1 else 0.0

        if len(var_values) >= 2:
            trend_dir = "increasing" if var_values[-1] > var_values[0] else "decreasing"
        else:
            trend_dir = "stable"

        return {
            "status": "success",
            "trend_direction": trend_dir,
            "volatility_of_var": vol_val,
            "mean_var": mean_val,
            "data_points_analyzed": len(records)
        }

    def evaluate_stress_trend(self, portfolio_uuid, scenario_name):
        stream_data = self.market_portfolio_scenario_simulator.run_monte_carlo(portfolio_uuid, scenario_name)
        if isinstance(stream_data, io.BytesIO):
            payload = json.loads(stream_data.read().decode('utf-8'))
        else:
            payload = stream_data

        impact = payload.get("impact", 0.0)
        return {
            "scenario_evaluated": scenario_name,
            "simulated_impact": impact
        }

    def generate_trend_audit_payload(self, report_uuid, risk_metric, threshold):
        return {
            "report_uuid": report_uuid,
            "metric_monitored": risk_metric,
            "alert_threshold": threshold,
            "export_timestamp": datetime.utcnow().isoformat()
        }


def analyze_var_and_stress_trends(run_id, portfolio_id, confidence, historical_window_days, scenario_data):
    impacts = []
    if isinstance(scenario_data, dict):
        impacts = scenario_data.get("simulated_impacts", [0.01, 0.02, 0.03])
    elif isinstance(scenario_data, list):
        impacts = scenario_data
    else:
        impacts = [0.01, 0.02]

    trend_slope = statistics.mean(impacts) if impacts else 0.0
    risk_velocity = statistics.pstdev(impacts) if len(impacts) > 1 else 0.0

    return {
        "run_id": run_id,
        "portfolio_id": portfolio_id,
        "confidence": confidence,
        "historical_window_days": historical_window_days,
        "trend_slope": trend_slope,
        "risk_velocity": risk_velocity,
        "timestamp": datetime.utcnow().isoformat()
    }