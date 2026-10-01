import json
try:
    import requests
except ImportError:
    requests = None
import time
import uuid

from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator

class MarketPortfolioVarTelemetryCollector:
    def __init__(self, db_storage=None, market_portfolio_monitor=None, market_portfolio_api_gateway=None):
        self.db_storage = db_storage
        self.market_portfolio_monitor = market_portfolio_monitor
        self.market_portfolio_api_gateway = market_portfolio_api_gateway

    def collect_from_stream(self, raw_stream):
        content = raw_stream.read()
        payload = json.loads(content.decode('utf-8'))

        simulation_id = payload.get("simulation_id")
        var_value = payload.get("var_value")

        success = self.db_storage.save_telemetry(payload)
        return success

    def push_metric_to_dashboard(self, endpoint_url, metric_name, value):
        if requests is None:
            return {"status": "accepted", "metric": metric_name, "value": value}
        response = requests.post(endpoint_url, json={"metric": metric_name, "value": value})
        return response.json()

    def aggregate_window(self, window_id):
        records = self.db_storage.fetch_window_metrics(window_id)
        if not records:
            return {"average_var": 0.0, "sample_count": 0}

        total_var = sum(r.get("var_value", 0.0) for r in records)
        count = len(records)
        avg_var = total_var / count if count > 0 else 0.0

        return {
            "average_var": avg_var,
            "sample_count": count
        }

    def process_anomaly_alert(self, anomaly_event):
        return self.notify_gateway(anomaly_event)

    def notify_gateway(self, anomaly_event):
        if self.market_portfolio_api_gateway:
            return self.market_portfolio_api_gateway.send(anomaly_event)
        return True


def market_portfolio_var_telemetry_collector(payload):
    run_id = payload.get("run_id")
    simulation_id = payload.get("simulation_id")
    scenario_output = payload.get("scenario_output")

    if not scenario_output:
        sim_input = {
            "simulation_id": simulation_id,
            "run_id": run_id,
            "confidence": payload.get("confidence", 0.95),
            "initial_capital": payload.get("initial_capital", 100000.0),
            "horizon_days": payload.get("horizon_days", 1)
        }
        scenario_output = market_portfolio_scenario_simulator(sim_input)

    var_result = scenario_output.get("var_result", {})
    portfolio_value = var_result.get("portfolio_value", 100000.0)

    telemetry_id = str(uuid.uuid4())

    record = {
        "telemetry_id": telemetry_id,
        "run_id": run_id,
        "simulation_id": simulation_id,
        "portfolio_value": portfolio_value,
        "timestamp": payload.get("timestamp", time.time())
    }

    from skills.db_storage import db_storage
    db_storage({"action": "save", "table": "var_telemetry", "id": telemetry_id, "data": record})

    return {
        "run_id": run_id,
        "simulation_id": simulation_id,
        "telemetry_id": telemetry_id
    }
