import unittest
from unittest.mock import patch, MagicMock
import os
import json
import uuid
import random
import tempfile
from skills.market_portfolio_stress_stress_dashboard_exporter import (
    MarketPortfolioStressDashboardExporter,
    export_stress_dashboard
)

class TestMarketPortfolioStressDashboardExporter(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.format_type = random.choice(["json", "csv"])
        self.temp_dir = tempfile.TemporaryDirectory()
        self.destination_path = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.{self.format_type}")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_init_defaults(self):
        exporter = MarketPortfolioStressDashboardExporter()
        self.assertIsNone(exporter.db_storage)
        self.assertIsNone(exporter.stress_reporter)
        self.assertIsNone(exporter.monte_carlo_engine)

    def test_export_dashboard_invalid_format(self):
        exporter = MarketPortfolioStressDashboardExporter()
        invalid_format = uuid.uuid4().hex[:4]
        with self.assertRaises(ValueError):
            exporter.export_dashboard_data(self.portfolio_id, invalid_format, self.destination_path)

    def test_build_payload_with_reporters(self):
        mock_reporter = MagicMock()
        expected_stress = {uuid.uuid4().hex: random.random()}
        mock_reporter.get_aggregated_stress_data.return_value = expected_stress

        mock_mc = MagicMock()
        expected_mc = {uuid.uuid4().hex: random.random()}
        mock_mc.get_simulation_metrics.return_value = expected_mc

        exporter = MarketPortfolioStressDashboardExporter(
            market_portfolio_stress_reporter=mock_reporter,
            market_portfolio_stress_monte_carlo_engine=mock_mc
        )

        payload = exporter._build_payload(self.portfolio_id)
        self.assertEqual(payload["portfolio_id"], self.portfolio_id)
        self.assertEqual(payload["stress_data"], expected_stress)
        self.assertEqual(payload["monte_carlo_metrics"], expected_mc)
        self.assertIn("timestamp", payload)

    def test_build_payload_fallback_breakdown_and_intervals(self):
        mock_reporter = MagicMock()
        del mock_reporter.get_aggregated_stress_data
        expected_breakdown = [{uuid.uuid4().hex: random.randint(1, 100)}]
        mock_reporter.get_scenario_breakdown.return_value = expected_breakdown

        mock_mc = MagicMock()
        del mock_mc.get_simulation_metrics
        expected_ci = {uuid.uuid4().hex: random.uniform(0, 1)}
        mock_mc.get_confidence_intervals.return_value = expected_ci

        exporter = MarketPortfolioStressDashboardExporter(
            market_portfolio_stress_reporter=mock_reporter,
            market_portfolio_stress_monte_carlo_engine=mock_mc
        )

        payload = exporter._build_payload(self.portfolio_id)
        self.assertEqual(payload["stress_data"], {"scenario_breakdown": expected_breakdown})
        self.assertEqual(payload["monte_carlo_metrics"], expected_ci)

    def test_build_payload_db_fallback(self):
        mock_db = MagicMock()
        expected_pipeline = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_monte_carlo = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_stress_dashboard_exporter.get_from_database") as mock_get_db:
            mock_get_db.return_value = {
                "pipeline": expected_pipeline,
                "monte_carlo": expected_monte_carlo
            }
            exporter = MarketPortfolioStressDashboardExporter()
            payload = exporter._build_payload(self.portfolio_id)

            self.assertEqual(payload["stress_data"], expected_pipeline)
            self.assertEqual(payload["monte_carlo_metrics"], expected_monte_carlo)

    def test_export_dashboard_json(self):
        mock_db = MagicMock()
        exporter = MarketPortfolioStressDashboardExporter(db_storage=mock_db)

        result = exporter.export_dashboard_data(self.portfolio_id, "json", self.destination_path)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.destination_path))

        mock_db.log_export_event.assert_called_once_with(self.portfolio_id, "json", self.destination_path)

        with open(self.destination_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["portfolio_id"], self.portfolio_id)

    def test_export_dashboard_csv(self):
        mock_reporter = MagicMock()
        stress_key = uuid.uuid4().hex
        stress_val = uuid.uuid4().hex
        mock_reporter.get_aggregated_stress_data.return_value = {stress_key: stress_val}

        exporter = MarketPortfolioStressDashboardExporter(
            market_portfolio_stress_reporter=mock_reporter
        )

        with patch("skills.market_portfolio_stress_stress_dashboard_exporter.log_export_event") as mock_log:
            result = exporter.export_dashboard_data(self.portfolio_id, "csv", self.destination_path)
            self.assertTrue(result)
            self.assertTrue(os.path.exists(self.destination_path))
            mock_log.assert_called_once_with(self.portfolio_id, "csv", self.destination_path)

        with open(self.destination_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(f"stress_{stress_key}", content)
            self.assertIn(stress_val, content)

    def test_export_dashboard_csv_with_list_stress_data(self):
        mock_reporter = MagicMock()
        item_key = uuid.uuid4().hex
        item_val = uuid.uuid4().hex
        mock_reporter.get_aggregated_stress_data.return_value = [{item_key: item_val}, uuid.uuid4().hex]

        exporter = MarketPortfolioStressDashboardExporter(
            market_portfolio_stress_reporter=mock_reporter
        )

        result = exporter.export_dashboard_data(self.portfolio_id, "csv", self.destination_path)
        self.assertTrue(result)

        with open(self.destination_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(f"stress_item_0_{item_key}", content)
            self.assertIn(item_val, content)

    def test_export_stress_dashboard_wrapper(self):
        output_path = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        params = {
            "portfolio_id": self.portfolio_id,
            "format": "json",
            "output_path": output_path
        }

        with patch("skills.market_portfolio_stress_stress_dashboard_exporter.MarketPortfolioStressDashboardExporter.export_dashboard_data") as mock_export:
            mock_export.return_value = True
            res = export_stress_dashboard(params)

            self.assertTrue(res["success"])
            self.assertEqual(res["output_path"], output_path)
            mock_export.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                format_type="json",
                destination_path=output_path
            )

    def test_export_stress_dashboard_wrapper_default_format(self):
        output_path = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        params = {
            "portfolio_id": self.portfolio_id,
            "output_path": output_path
        }

        with patch("skills.market_portfolio_stress_stress_dashboard_exporter.MarketPortfolioStressDashboardExporter.export_dashboard_data") as mock_export:
            mock_export.return_value = True
            res = export_stress_dashboard(params)

            self.assertTrue(res["success"])
            mock_export.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                format_type="json",
                destination_path=output_path
            )
