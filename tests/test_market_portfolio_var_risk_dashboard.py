import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import json

from skills.market_portfolio_var_risk_dashboard import (
    generate_var_risk_dashboard,
    aggregate_monte_carlo_metrics,
    VaRRiskDashboardException
)

class TestMarketPortfolioVaRRiskDashboard(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.confidence_level = round(random.uniform(0.90, 0.99), 4)
        self.simulation_runs = random.randint(1000, 50000)
        self.initial_portfolio_value = round(random.uniform(10000.0, 1000000.0), 2)
        self.mock_db = MagicMock()
        self.mock_monte_carlo_engine = MagicMock()
        self.mock_stress_reporter = MagicMock()

    def test_generate_var_risk_dashboard_success(self):
        random_var_value = round(random.uniform(500.0, 50000.0), 2)
        random_cvar_value = round(random_var_value * random.uniform(1.1, 1.5), 2)
        random_max_drawdown = round(random.uniform(0.05, 0.45), 4)

        sim_results = {
            "portfolio_id": self.portfolio_id,
            "var": random_var_value,
            "cvar": random_cvar_value,
            "max_drawdown": random_max_drawdown,
            "confidence": self.confidence_level,
            "runs": self.simulation_runs
        }

        with patch("skills.market_portfolio_var_risk_dashboard.market_portfolio_stress_monte_carlo_engine") as mock_mc_engine, \
             patch("skills.market_portfolio_var_risk_dashboard.market_portfolio_stress_reporter") as mock_reporter, \
             patch("skills.market_portfolio_var_risk_dashboard.db_storage") as mock_storage:

            mock_mc_engine.run_simulation.return_value = sim_results
            mock_reporter.compile_report.return_value = {"status": "compiled", "id": self.portfolio_id}
            mock_storage.save_dashboard.return_value = True

            result = generate_var_risk_dashboard(
                portfolio_id=self.portfolio_id,
                initial_value=self.initial_portfolio_value,
                confidence=self.confidence_level,
                simulations=self.simulation_runs
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
            self.assertEqual(result.get("var"), random_var_value)
            self.assertEqual(result.get("cvar"), random_cvar_value)
            self.assertEqual(result.get("max_drawdown"), random_max_drawdown)
            mock_mc_engine.run_simulation.assert_called_once()
            mock_storage.save_dashboard.assert_called_once()

    def test_aggregate_monte_carlo_metrics_random_data(self):
        random_returns = [round(random.gauss(-0.001, 0.02), 5) for _ in range(100)]
        stream_data = io.BytesIO(json.dumps(random_returns).encode('utf-8'))

        with patch("skills.market_portfolio_var_risk_dashboard.market_portfolio_data_exporter") as mock_exporter:
            mock_exporter.fetch_simulation_stream.return_value = stream_data

            aggregated = aggregate_monte_carlo_metrics(
                portfolio_id=self.portfolio_id,
                confidence=self.confidence_level
            )

            self.assertIsInstance(aggregated, dict)
            self.assertIn("var_calculated", aggregated)
            self.assertIn("expected_shortfall", aggregated)
            self.assertIsInstance(aggregated["var_calculated"], float)
            self.assertIsInstance(aggregated["expected_shortfall"], float)

    def test_generate_var_risk_dashboard_exception_handling(self):
        random_error_message = ''.join(random.choices(string.ascii_letters + string.digits, k=25))

        with patch("skills.market_portfolio_var_risk_dashboard.market_portfolio_stress_monte_carlo_engine") as mock_mc_engine:
            mock_mc_engine.run_simulation.side_effect = Exception(random_error_message)

            with self.assertRaises(VaRRiskDashboardException) as ctx:
                generate_var_risk_dashboard(
                    portfolio_id=self.portfolio_id,
                    initial_value=self.initial_portfolio_value,
                    confidence=self.confidence_level,
                    simulations=self.simulation_runs
                )

            self.assertIn(random_error_message, str(ctx.exception))

    def test_dashboard_stream_integration_with_random_payload(self):
        random_string_payload = ''.join(random.choices(string.ascii_letters, k=50))
        binary_payload = io.BytesIO(random_string_payload.encode('utf-8'))

        with patch("skills.market_portfolio_var_risk_dashboard.market_portfolio_audit_log_exporter") as mock_logger:
            mock_logger.export_raw_stream.return_value = binary_payload

            from skills.market_portfolio_var_risk_dashboard import audit_dashboard_data_stream
            stream_result = audit_dashboard_data_stream(portfolio_id=self.portfolio_id)

            self.assertEqual(stream_result, random_string_payload)
            mock_logger.export_raw_stream.assert_called_once_with(portfolio_id=self.portfolio_id)

if __name__ == '__main__':
    unittest.main()