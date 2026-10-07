import json
import csv
import datetime
from typing import Dict, Any, Union

from skills.db_storage import get_from_database, save_to_database, log_export_event


class MarketPortfolioStressDashboardExporter:
    def __init__(
        self,
        db_storage: Any = None,
        market_portfolio_stress_reporter: Any = None,
        market_portfolio_stress_monte_carlo_engine: Any = None,
    ):
        self.db_storage = db_storage
        self.stress_reporter = market_portfolio_stress_reporter
        self.monte_carlo_engine = market_portfolio_stress_monte_carlo_engine

    def _build_payload(self, portfolio_id: str) -> Dict[str, Any]:
        stress_data = {}
        if self.stress_reporter and hasattr(self.stress_reporter, "get_aggregated_stress_data"):
            stress_data = self.stress_reporter.get_aggregated_stress_data(portfolio_id)
        elif self.stress_reporter and hasattr(self.stress_reporter, "get_scenario_breakdown"):
            breakdown = self.stress_reporter.get_scenario_breakdown(portfolio_id)
            stress_data = {"scenario_breakdown": breakdown}
        else:
            record = None
            if self.db_storage and hasattr(self.db_storage, "get_from_database"):
                record = self.db_storage.get_from_database("stress_test_runs", portfolio_id)
            if not record:
                record = get_from_database("stress_test_runs", portfolio_id)
            if record and isinstance(record, dict) and "pipeline" in record:
                stress_data = record["pipeline"]

        monte_carlo_metrics = {}
        if self.monte_carlo_engine and hasattr(self.monte_carlo_engine, "get_simulation_metrics"):
            monte_carlo_metrics = self.monte_carlo_engine.get_simulation_metrics(portfolio_id)
        elif self.monte_carlo_engine and hasattr(self.monte_carlo_engine, "get_confidence_intervals"):
            monte_carlo_metrics = self.monte_carlo_engine.get_confidence_intervals(portfolio_id)
        else:
            record = None
            if self.db_storage and hasattr(self.db_storage, "get_from_database"):
                record = self.db_storage.get_from_database("stress_test_runs", portfolio_id)
            if not record:
                record = get_from_database("stress_test_runs", portfolio_id)
            if record and isinstance(record, dict) and "monte_carlo" in record:
                monte_carlo_metrics = record["monte_carlo"]

        return {
            "portfolio_id": portfolio_id,
            "stress_data": stress_data,
            "monte_carlo_metrics": monte_carlo_metrics,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }

    def export_dashboard_data(
        self, portfolio_id: str, format_type: str, destination_path: str
    ) -> bool:
        if format_type not in ["json", "csv"]:
            raise ValueError(f"Invalid format type: {format_type}")

        if self.db_storage and hasattr(self.db_storage, "log_export_event"):
            self.db_storage.log_export_event(portfolio_id, format_type, destination_path)
        else:
            log_export_event(portfolio_id, format_type, destination_path)

        payload = self._build_payload(portfolio_id)

        if format_type == "json":
            with open(destination_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        elif format_type == "csv":
            with open(destination_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["key", "value"])
                writer.writerow(["portfolio_id", payload.get("portfolio_id")])
                writer.writerow(["timestamp", payload.get("timestamp")])

                stress_data = payload.get("stress_data", {})
                if isinstance(stress_data, dict):
                    for k, v in stress_data.items():
                        writer.writerow([f"stress_{k}", v])
                elif isinstance(stress_data, list):
                    for idx, item in enumerate(stress_data):
                        if isinstance(item, dict):
                            for k, v in item.items():
                                writer.writerow([f"stress_item_{idx}_{k}", v])
                        else:
                            writer.writerow([f"stress_item_{idx}", item])

                mc_metrics = payload.get("monte_carlo_metrics", {})
                if isinstance(mc_metrics, dict):
                    for k, v in mc_metrics.items():
                        writer.writerow([f"mc_{k}", v])

        return True


def export_stress_dashboard(params: dict) -> dict:
    portfolio_id = params.get("portfolio_id")
    format_type = params.get("format", "json")
    output_path = params.get("output_path")

    exporter = MarketPortfolioStressDashboardExporter()
    success = exporter.export_dashboard_data(
        portfolio_id=portfolio_id,
        format_type=format_type,
        destination_path=output_path
    )

    return {"success": success, "output_path": output_path}
