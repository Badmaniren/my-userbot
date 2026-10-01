import unittest
import uuid
import random
import os
import tempfile
from skills.market_portfolio_stress_dashboard_api import market_portfolio_stress_dashboard_api
from skills.db_storage import db_storage
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.market_portfolio_stress_reporter import market_portfolio_stress_reporter

class TestMarketPortfolioStressDashboardApiIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.test_dir.name, f"test_db_{uuid.uuid4()}.db")
        self.portfolio_id = f"port_{uuid.uuid4()}"
        self.scenario_id = f"scen_{uuid.uuid4()}"
        self.shock_magnitude = round(random.uniform(-0.5, -0.05), 4)
        self.confidence_level = random.choice([0.95, 0.99])
        self.simulations_count = random.randint(100, 1000)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_stress_dashboard_pipeline_integration(self):
        db_instance = db_storage()
        db_init_result = db_instance.initialize(self.db_path)
        self.assertTrue(db_init_result, "Database initialization failed")

        simulator = market_portfolio_scenario_simulator()
        scenario_data = {
            "portfolio_id": self.portfolio_id,
            "scenario_id": self.scenario_id,
            "shock_magnitude": self.shock_magnitude,
            "target_asset": "SYNTH_INDEX"
        }
        simulation_result = simulator.run_simulation(scenario_data)
        self.assertIsNotNone(simulation_result, "Scenario simulation returned None")

        mc_engine = market_portfolio_stress_monte_carlo_engine()
        mc_config = {
            "portfolio_id": self.portfolio_id,
            "confidence_level": self.confidence_level,
            "simulations": self.simulations_count
        }
        mc_result = mc_engine.calculate_var_monte_carlo(mc_config)
        self.assertIsNotNone(mc_result, "Monte Carlo engine returned None")

        reporter = market_portfolio_stress_reporter()
        report_payload = {
            "portfolio_id": self.portfolio_id,
            "simulation": simulation_result,
            "monte_carlo": mc_result
        }
        report_id = reporter.generate_report(report_payload)
        self.assertIsNotNone(report_id, "Stress reporter failed to generate report ID")

        dashboard_api = market_portfolio_stress_dashboard_api()
        dashboard_query = {
            "portfolio_id": self.portfolio_id,
            "report_id": report_id,
            "include_telemetry": True
        }
        dashboard_response = dashboard_api.aggregate_dashboard_metrics(dashboard_query)

        self.assertIsInstance(dashboard_response, dict, "Dashboard API must return a dictionary payload")
        self.assertEqual(dashboard_response.get("portfolio_id"), self.portfolio_id, "Portfolio ID mismatch in dashboard response")
        self.assertEqual(dashboard_response.get("report_id"), report_id, "Report ID mismatch in dashboard response")
        self.assertIn("aggregated_metrics", dashboard_response, "Missing aggregated metrics in dashboard response")

        stored_record = db_instance.get_record(self.db_path, self.portfolio_id)
        self.assertIsNotNone(stored_record, "Integrated workflow failed to persist state into db_storage")

if __name__ == "__main__":
    unittest.main()