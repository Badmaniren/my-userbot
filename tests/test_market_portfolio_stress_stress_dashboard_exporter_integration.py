import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_stress_stress_dashboard_exporter import (
    MarketPortfolioStressDashboardExporter,
    export_stress_dashboard
)
from skills.market_portfolio_stress_reporter import MarketPortfolioStressReporter
from skills.market_portfolio_stress_monte_carlo_engine import MarketPortfolioStressMonteCarloEngine
from skills.db_storage import save_to_database


class TestMarketPortfolioStressDashboardExporterIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.json_path = f"test_dashboard_{uuid.uuid4().hex[:8]}.json"
        self.csv_path = f"test_dashboard_{uuid.uuid4().hex[:8]}.csv"

        self.stress_value = round(random.uniform(-0.5, -0.1), 4)
        self.mc_value = round(random.uniform(1000.0, 50000.0), 2)

        stress_record = {
            "pipeline": {
                "var_95": self.stress_value,
                "max_drawdown": -0.25
            }
        }
        monte_carlo_record = {
            "monte_carlo": {
                "expected_shortfall": self.mc_value,
                "confidence": 0.99
            }
        }

        save_to_database("stress_test_runs", self.portfolio_id, {
            "pipeline": stress_record["pipeline"],
            "monte_carlo": monte_carlo_record["monte_carlo"]
        })

    def tearDown(self):
        for path in [self.json_path, self.csv_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_integration_exporter_json(self):
        reporter = MarketPortfolioStressReporter()
        monte_carlo = MarketPortfolioStressMonteCarloEngine()

        exporter = MarketPortfolioStressDashboardExporter(
            market_portfolio_stress_reporter=reporter,
            market_portfolio_stress_monte_carlo_engine=monte_carlo
        )

        success = exporter.export_dashboard_data(
            portfolio_id=self.portfolio_id,
            format_type="json",
            destination_path=self.json_path
        )

        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.json_path))

        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("portfolio_id"), self.portfolio_id)
        self.assertIn("timestamp", data)
        self.assertIsInstance(data.get("stress_data"), dict)
        self.assertIsInstance(data.get("monte_carlo_metrics"), dict)

    def test_integration_exporter_csv(self):
        exporter = MarketPortfolioStressDashboardExporter()

        params = {
            "portfolio_id": self.portfolio_id,
            "format": "csv",
            "output_path": self.csv_path
        }

        result = export_stress_dashboard(params)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("output_path"), self.csv_path)
        self.assertTrue(os.path.exists(self.csv_path))

        with open(self.csv_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(self.portfolio_id, content)
        self.assertIn("key,value", content)
        self.assertIn("portfolio_id", content)


if __name__ == "__main__":
    unittest.main()