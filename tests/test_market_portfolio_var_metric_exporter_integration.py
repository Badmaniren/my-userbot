import unittest
import uuid
import random
import os
import json
from skills.market_portfolio_var_metric_exporter import MarketPortfolioVarMetricExporter, export_var_and_monte_carlo_metrics
from skills.market_portfolio_stress_monte_carlo_engine import run_monte_carlo_stress_test


class TestMarketPortfolioVarMetricExporterIntegration(unittest.TestCase):
    def test_export_var_and_monte_carlo_metrics_integration(self):
        portfolio_id = str(uuid.uuid4())
        random_confidence = round(random.uniform(0.90, 0.99), 4)
        random_var_value = round(random.uniform(1000.0, 500000.0), 2)

        monte_carlo_result = run_monte_carlo_stress_test(portfolio_id=portfolio_id, simulations=100)

        metrics_payload = {
            "confidence_level": random_confidence,
            "var_value": random_var_value,
            "monte_carlo_simulation_summary": monte_carlo_result
        }

        export_result = export_var_and_monte_carlo_metrics(
            portfolio_id=portfolio_id,
            metrics_payload=metrics_payload,
            format_type="json"
        )

        self.assertTrue(export_result.get("success"))
        file_path = export_result.get("file_path")
        self.assertTrue(os.path.exists(file_path))

        with open(file_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data.get("portfolio_id"), portfolio_id)
        self.assertEqual(saved_data.get("confidence_level"), random_confidence)
        self.assertEqual(saved_data.get("var_value"), random_var_value)
        self.assertIn("monte_carlo_simulation_summary", saved_data)

        if os.path.exists(file_path):
            os.remove(file_path)

    def test_exporter_class_initialization_and_exceptions(self):
        portfolio_id = str(uuid.uuid4())
        confidence_level = random.choice([0.95, 0.99])

        exporter = MarketPortfolioVarMetricExporter(db_storage=None)
        with self.assertRaises(NotImplementedError):
            exporter.export_var_metric(portfolio_id, confidence_level)


if __name__ == "__main__":
    unittest.main()