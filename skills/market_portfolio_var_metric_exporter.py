import json
import os
import tempfile
import io
from skills.market_portfolio_stress_monte_carlo_engine import run_monte_carlo_stress_test


class MarketPortfolioVarMetricExporter:
    def __init__(self, db_storage=None):
        self.db_storage = db_storage

    def export_var_metric(self, portfolio_id: str, confidence_level: float) -> dict:
        if self.db_storage is not None:
            return self.db_storage.fetch_var_metric(portfolio_id, confidence_level)
        raise NotImplementedError("db_storage is required for this operation")

    def export_monte_carlo_stream(self, scenario_id: str) -> io.BytesIO:
        return self._get_monte_carlo_stream(scenario_id)

    def _get_monte_carlo_stream(self, scenario_id: str) -> io.BytesIO:
        pass


def export_var_and_monte_carlo_metrics(portfolio_id: str, metrics_payload: dict, format_type: str = "json") -> dict:
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, f"var_metric_{portfolio_id}.json")

    payload_to_save = dict(metrics_payload)
    payload_to_save["portfolio_id"] = portfolio_id

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload_to_save, f)

    return {
        "success": True,
        "file_path": file_path
    }