import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
import json
import csv

from skills.market_portfolio_stress_simulation_exporter import StressSimulationExporter


class TestMarketPortfolioStressSimulationExporter(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.scenario_simulator = MagicMock()
        self.stress_reporter = MagicMock()
        self.exporter = StressSimulationExporter(
            db_storage=self.db_storage,
            scenario_simulator=self.scenario_simulator,
            stress_reporter=self.stress_reporter
        )

    def _generate_random_simulation_data(self):
        return {
            "simulation_id": str(uuid.uuid4()),
            "scenario_name": ''.join(random.choices(string.ascii_letters, k=10)),
            "portfolio_value": round(random.uniform(10000.0, 1000000.0), 2),
            "stressed_value": round(random.uniform(5000.0, 900000.0), 2),
            "max_drawdown": round(random.uniform(0.01, 0.99), 4),
            "risk_metrics": {
                "var_95": round(random.uniform(100.0, 5000.0), 2),
                "cvar_95": round(random.uniform(200.0, 8000.0), 2)
            }
        }

    def test_export_to_json_success(self):
        raw_data = self._generate_random_simulation_data()
        target_uuid = raw_data["simulation_id"]

        self.db_storage.get_simulation.return_value = raw_data

        random_filepath = f"/tmp/{uuid.uuid4().hex}.json"
        mock_file = MagicMock()

        with patch("builtins.open", return_value=mock_file) as mock_open:
            result = self.exporter.export_json(target_uuid, random_filepath)

            mock_open.assert_called_once_with(random_filepath, 'w', encoding='utf-8')
            mock_file.__enter__().write.assert_called_once()
            self.assertTrue(result)

            written_content = mock_file.__enter__().write.call_args[0][0]
            parsed_json = json.loads(written_content)
            self.assertEqual(parsed_json["simulation_id"], target_uuid)
            self.assertEqual(parsed_json["portfolio_value"], raw_data["portfolio_value"])

    def test_export_to_csv_success(self):
        raw_data = self._generate_random_simulation_data()
        target_uuid = raw_data["simulation_id"]

        self.db_storage.get_simulation.return_value = raw_data

        random_filepath = f"/tmp/{uuid.uuid4().hex}.csv"
        mock_file = io.StringIO()
        mock_file.close = MagicMock()

        with patch("builtins.open", return_value=mock_file) as mock_open:
            result = self.exporter.export_csv(target_uuid, random_filepath)

            mock_open.assert_called_once_with(random_filepath, 'w', newline='', encoding='utf-8')
            self.assertTrue(result)

            mock_file.seek(0)
            content = mock_file.read()
            self.assertIn(target_uuid, content)
            self.assertIn(str(raw_data["portfolio_value"]), content)

    def test_export_to_html_report_success(self):
        raw_data = self._generate_random_simulation_data()
        target_uuid = raw_data["simulation_id"]
        random_title = ''.join(random.choices(string.ascii_letters, k=8))

        self.db_storage.get_simulation.return_value = raw_data
        self.stress_reporter.generate_html_template.return_value = f"<html><body><h1>{random_title}</h1><p>{target_uuid}</p></body></html>"

        random_filepath = f"/tmp/{uuid.uuid4().hex}.html"
        mock_file = MagicMock()

        with patch("builtins.open", return_value=mock_file) as mock_open:
            result = self.exporter.export_html_report(target_uuid, random_filepath)

            mock_open.assert_called_once_with(random_filepath, 'w', encoding='utf-8')
            mock_file.__enter__().write.assert_called_once()
            self.assertTrue(result)

            written_html = mock_file.__enter__().write.call_args[0][0]
            self.assertIn(target_uuid, written_html)
            self.assertIn(random_title, written_html)

    def test_export_simulation_not_found(self):
        non_existent_uuid = str(uuid.uuid4())
        self.db_storage.get_simulation.return_value = None

        random_filepath = f"/tmp/{uuid.uuid4().hex}.json"

        with patch("builtins.open") as mock_open:
            result = self.exporter.export_json(non_existent_uuid, random_filepath)
            mock_open.assert_not_called()
            self.assertFalse(result)

    def test_batch_export_analytics_payload(self):
        batch_size = random.randint(2, 5)
        simulations = [self._generate_random_simulation_data() for _ in range(batch_size)]
        target_uuids = [sim["simulation_id"] for sim in simulations]

        self.db_storage.get_simulations_batch.return_value = simulations

        random_stream = io.BytesIO()

        with patch("zipfile.ZipFile") as mock_zip_class:
            mock_zip_instance = mock_zip_class.return_value.__enter__.return_value

            result = self.exporter.export_batch_archive(target_uuids, random_stream)

            self.assertTrue(result)
            self.assertEqual(mock_zip_instance.writestr.call_count, batch_size)

            written_names = [call[0][0] for call in mock_zip_instance.writestr.call_args_list]
            for uid in target_uuids:
                self.assertTrue(any(uid in name for name in written_names))