import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import os
from skills.market_portfolio_var_metric_exporter import (
    MarketPortfolioVarMetricExporter,
    export_var_and_monte_carlo_metrics
)


class TestMarketPortfolioVarMetricExporter(unittest.TestCase):

    def test_export_var_metric_success(self):
        portfolio_id = uuid.uuid4().hex
        confidence_level = round(random.uniform(0.9, 0.99), 4)
        expected_result = {
            "portfolio_id": portfolio_id,
            "confidence_level": confidence_level,
            "var_value": random.uniform(1000.0, 50000.0)
        }

        mock_db = MagicMock()
        mock_db.fetch_var_metric.return_value = expected_result

        exporter = MarketPortfolioVarMetricExporter(db_storage=mock_db)
        result = exporter.export_var_metric(portfolio_id, confidence_level)

        mock_db.fetch_var_metric.assert_called_once_with(portfolio_id, confidence_level)
        self.assertEqual(result, expected_result)

    def test_export_var_metric_no_storage(self):
        portfolio_id = uuid.uuid4().hex
        confidence_level = round(random.uniform(0.9, 0.99), 4)

        exporter = MarketPortfolioVarMetricExporter(db_storage=None)
        with self.assertRaises(NotImplementedError):
            exporter.export_var_metric(portfolio_id, confidence_level)

    def test_export_monte_carlo_stream(self):
        scenario_id = uuid.uuid4().hex
        exporter = MarketPortfolioVarMetricExporter()

        with patch.object(exporter, '_get_monte_carlo_stream') as mock_method:
            fake_stream = io.BytesIO(uuid.uuid4().bytes)
            mock_method.return_value = fake_stream

            res = exporter.export_monte_carlo_stream(scenario_id)
            mock_method.assert_called_once_with(scenario_id)
            self.assertEqual(res, fake_stream)


class TestExportVarAndMonteCarloMetricsIntegration(unittest.TestCase):

    def test_export_var_and_monte_carlo_metrics(self):
        portfolio_id = uuid.uuid4().hex
        key_metric = uuid.uuid4().hex
        val_metric = random.randint(100, 9999)
        metrics_payload = {key_metric: val_metric}

        result = export_var_and_monte_carlo_metrics(portfolio_id, metrics_payload, format_type="json")

        self.assertTrue(result.get("success"))
        file_path = result.get("file_path")
        self.assertTrue(os.path.exists(file_path))

        with open(file_path, "r", encoding="utf-8") as f:
            import json
            data = json.load(f)

        self.assertEqual(data.get("portfolio_id"), portfolio_id)
        self.assertEqual(data.get(key_metric), val_metric)

        if os.path.exists(file_path):
            os.remove(file_path)


if __name__ == "__main__":
    unittest.main()