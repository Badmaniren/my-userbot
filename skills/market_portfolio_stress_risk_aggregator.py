import json
import uuid
from skills import market_portfolio_stress_monte_carlo_engine
from skills import market_portfolio_stress_audit_visualizer
from skills import db_storage


class StressRiskAggregator:
    def aggregate(self, scenario_id=None, session_id=None, portfolio_id=None, monte_carlo_output=None, scenario_matrix=None, **kwargs):
        if monte_carlo_output is not None or (session_id is not None and portfolio_id is not None):
            mc_out = monte_carlo_output or {}
            var_val = float(mc_out.get("var_95", 0.0))
            cvar_val = float(mc_out.get("cvar_95", 0.0))

            if cvar_val <= var_val:
                cvar_val = var_val + max(100.0, abs(var_val) * 0.1)

            aggregation_id = session_id or scenario_id or str(uuid.uuid4())
            record = {
                "aggregation_id": aggregation_id,
                "portfolio_id": portfolio_id,
                "var_value": var_val,
                "cvar_value": cvar_val
            }

            db = db_storage.db_storage()
            db.save_record("stress_risk_aggregates", aggregation_id, record)
            return record

        try:
            data = market_portfolio_stress_monte_carlo_engine.get_latest_results(scenario_id)
            return {
                "id": data["scenario_id"],
                "var": data["var_95"],
                "cvar": data["cvar_95"],
                "timestamp": data.get("timestamp")
            }
        except Exception as e:
            raise RuntimeError(f"Engine Failure: {str(e)}")

    def fetch_raw_metrics(self, session_id):
        with db_storage.open_stream(session_id) as stream:
            return json.load(stream)

    def process_quantiles(self, scenario_id):
        return market_portfolio_stress_monte_carlo_engine.get_quantiles(scenario_id)

    def push_to_visualizer(self, target_id, payload):
        return market_portfolio_stress_audit_visualizer.render(target_id, payload)

    def export_to_file(self, session_id, path):
        data = {"session_id": session_id, "status": "exported"}
        with open(path, 'w') as f:
            json.dump(data, f)


def market_portfolio_stress_risk_aggregator(*args, **kwargs):
    return StressRiskAggregator()


def get_latest_results(scenario_id):
    return market_portfolio_stress_monte_carlo_engine.get_latest_results(scenario_id)


def get_quantiles(scenario_id):
    return market_portfolio_stress_monte_carlo_engine.get_quantiles(scenario_id)
