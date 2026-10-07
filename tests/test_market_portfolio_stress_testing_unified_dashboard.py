import unittest
from unittest.mock import patch
import uuid
import random
import io
import datetime

from skills.market_portfolio_stress_testing_unified_dashboard import (
    MarketPortfolioStressTestingUnifiedDashboard,
    market_portfolio_stress_testing_unified_dashboard
)


class TestMarketPortfolioStressTestingUnifiedDashboard(unittest.TestCase):

    def setUp(self):
        self.dashboard = MarketPortfolioStressTestingUnifiedDashboard()
        self.portfolio_id = str(uuid.uuid4())
        self.task_id = str(uuid.uuid4())
        self.event_token = str(uuid.uuid4())

    def test_aggregate_stress_metrics(self):
        mc_mock_data = {"simulation_id": str(uuid.uuid4()), "var_99": random.uniform(-1000, -100)}
        var_mock_data = {"var_val": random.uniform(-500, -50), "cvar_val": random.uniform(-800, -200)}
        scenario_mock_data = {"scenario_name": str(uuid.uuid4()), "impact": random.uniform(-0.5, 0.0)}

        with patch("skills.market_portfolio_stress_monte_carlo_engine.run_simulation", return_value=mc_mock_data) as mock_mc, \
             patch("skills.market_portfolio_var_liquidity_core.calculate_var", return_value=var_mock_data) as mock_var, \
             patch("skills.market_portfolio_stress_scenario_matrix_evaluator.evaluate", return_value=scenario_mock_data) as mock_scenario:

            result = self.dashboard.aggregate_stress_metrics(self.portfolio_id)

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["monte_carlo"], mc_mock_data)
            self.assertEqual(result["var_cvar"], var_mock_data)
            self.assertEqual(result["scenario_matrix"], scenario_mock_data)

            mock_mc.assert_called_once_with(self.portfolio_id)
            mock_var.assert_called_once_with(self.portfolio_id)
            mock_scenario.assert_called_once_with(self.portfolio_id)

    def test_visualize_dashboard(self):
        random_bytes = f"chart_{uuid.uuid4().hex}".encode("utf-8")
        expected_stream = io.BytesIO(random_bytes)

        with patch("skills.market_portfolio_stress_audit_visualizer.render", return_value=expected_stream) as mock_render:
            stream = self.dashboard.visualize_dashboard(self.task_id)

            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read(), random_bytes)
            mock_render.assert_called_once_with(self.task_id)

    def test_generate_audit_and_report(self):
        report_mock_data = {"status": random.choice([200, 201]), "token": self.event_token, "data": str(uuid.uuid4())}

        with patch("skills.market_portfolio_stress_reporter.generate_report", return_value=report_mock_data) as mock_report, \
             patch("skills.market_portfolio_audit_compliance_hub.log_event") as mock_log:

            result = self.dashboard.generate_audit_and_report(self.event_token)

            self.assertEqual(result, report_mock_data)
            mock_report.assert_called_once_with(self.event_token)
            mock_log.assert_called_once_with(self.event_token)

    def test_functional_interface_dashboard(self):
        input_data = {
            "portfolio_id": self.portfolio_id,
            "monte_carlo_metrics": {"runs": random.randint(100, 1000)},
            "var_metrics": {"confidence": 0.99},
            "scenario_metrics": {"shocks": [random.random()]}
        }

        with patch("skills.market_portfolio_stress_testing_unified_dashboard.db_storage") as mock_db:
            result = market_portfolio_stress_testing_unified_dashboard(input_data)

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("dashboard_id", result)
            self.assertEqual(result["monte_carlo_metrics"], input_data["monte_carlo_metrics"])
            self.assertEqual(result["var_metrics"], input_data["var_metrics"])
            self.assertEqual(result["scenario_metrics"], input_data["scenario_metrics"])

            mock_db.assert_called_once()
            call_args = mock_db.call_args[0][0]
            self.assertEqual(call_args["action"], "set")
            self.assertEqual(call_args["table"], "stress_dashboards")
            self.assertEqual(call_args["id"], result["dashboard_id"])
            self.assertEqual(call_args["data"], result)


if __name__ == "__main__":
    unittest.main()