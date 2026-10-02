import json
import csv
import zipfile
from typing import List, Dict, Any, Union, IO

try:
    from skills.db_storage import db_storage as default_db_storage
except ImportError:
    default_db_storage = None

try:
    from skills.market_portfolio_stress_scenario_pipeline import market_portfolio_stress_scenario_pipeline
except ImportError:
    market_portfolio_stress_scenario_pipeline = None


class StressSimulationExporter:
    def __init__(self, db_storage=None, scenario_simulator=None, stress_reporter=None):
        self.db_storage = db_storage
        self.scenario_simulator = scenario_simulator
        self.stress_reporter = stress_reporter

    def _flatten_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        flattened = {}
        for key, value in data.items():
            if isinstance(value, dict):
                for sub_key, sub_val in value.items():
                    flattened[f"{key}_{sub_key}"] = sub_val
            else:
                flattened[key] = value
        return flattened

    def export_json(self, simulation_id: str, filepath: str) -> bool:
        if self.db_storage is None:
            return False
        data = self.db_storage.get_simulation(simulation_id)
        if data is None:
            return False
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=4))
        return True

    def export_csv(self, simulation_id: str, filepath: str) -> bool:
        if self.db_storage is None:
            return False
        data = self.db_storage.get_simulation(simulation_id)
        if data is None:
            return False

        flat_data = self._flatten_data(data)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(list(flat_data.keys()))
            writer.writerow(list(flat_data.values()))
        return True

    def export_html_report(self, simulation_id: str, filepath: str) -> bool:
        if self.db_storage is None or self.stress_reporter is None:
            return False
        data = self.db_storage.get_simulation(simulation_id)
        if data is None:
            return False

        html_content = self.stress_reporter.generate_html_template(data)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return True

    def export_batch_archive(self, simulation_ids: List[str], stream_or_path: Union[str, IO[bytes]]) -> bool:
        if self.db_storage is None:
            return False

        simulations = self.db_storage.get_simulations_batch(simulation_ids)
        if not simulations:
            return False

        with zipfile.ZipFile(stream_or_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for sim in simulations:
                sim_id = sim.get("simulation_id", "unknown")
                sim_data_str = json.dumps(sim, ensure_ascii=False, indent=4)
                zip_file.writestr(f"simulation_{sim_id}.json", sim_data_str)
        return True


def market_portfolio_stress_simulation_exporter(
    simulation_id: str,
    output_format: str,
    destination_path: str
) -> bool:
    class FunctionalDbStorage:
        def get_simulation(self, sim_id):
            if callable(default_db_storage):
                return default_db_storage(record_id=sim_id, namespace="stress_simulation_results")
            return None

        def get_simulations_batch(self, sim_ids):
            if callable(default_db_storage):
                return [default_db_storage(record_id=sid, namespace="stress_simulation_results") for sid in sim_ids]
            return []

    class FunctionalReporter:
        def generate_html_template(self, data):
            sim_id = data.get("simulation_id", "")
            return f"<html><body><h1>Report</h1><p>{sim_id}</p></body></html>"

    exporter = StressSimulationExporter(
        db_storage=FunctionalDbStorage(),
        stress_reporter=FunctionalReporter()
    )

    fmt = output_format.lower()
    if fmt == "json":
        return exporter.export_json(simulation_id, destination_path)
    elif fmt == "csv":
        return exporter.export_csv(simulation_id, destination_path)
    elif fmt == "html":
        return exporter.export_html_report(simulation_id, destination_path)
    else:
        return False