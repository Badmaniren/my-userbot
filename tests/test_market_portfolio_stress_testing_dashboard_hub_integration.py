import unittest
import uuid
import random
import io
from skills.market_portfolio_stress_testing_dashboard_hub import start_new, market_portfolio_stress_testing_dashboard_hub
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine as real_mc_engine
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator as real_scenario_simulator
from skills.market_portfolio_stress_reporter import market_portfolio_stress_reporter as real_reporter
from skills.db_storage import db_storage as real_db_storage

class TestIntegrationMarketPortfolioStressTestingDashboardHub(unittest.TestCase):
    def test_dashboard_hub_integration_flow(self):
        rand_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        rand_simulations = random.randint(500, 5000)
        rand_confidence = round(random.uniform(0.90, 0.99), 2)
        
        test_stream = io.BytesIO(f"test_data_{uuid.uuid4().hex}".encode('utf-8'))

        result = start_new(
            portfolio_id=rand_portfolio_id,
            simulations=rand_simulations,
            confidence=rand_confidence,
            data_stream=test_stream,
            market_portfolio_stress_monte_carlo_engine=real_mc_engine,
            market_portfolio_scenario_simulator=real_scenario_simulator,
            market_portfolio_stress_reporter=real_reporter
        )

        self.assertEqual(result.get("status"), "completed")
        self.assertEqual(result.get("portfolio_id"), rand_portfolio_id)
        self.assertIn("dashboard_id", result)

        dash_id = result.get("dashboard_id")
        mc_data = result.get("monte_carlo")
        scen_data = result.get("scenario")

        hub_result = market_portfolio_stress_testing_dashboard_hub(
            dashboard_id=dash_id,
            portfolio_id=rand_portfolio_id,
            monte_carlo_data=mc_data,
            scenario_data=scen_data
        )

        self.assertEqual(hub_result.get("status"), "completed")
        self.assertEqual(hub_result.get("portfolio_id"), rand_portfolio_id)
        self.assertEqual(hub_result.get("dashboard_id"), dash_id)
        self.assertIn("aggregated_metrics", hub_result)
        self.assertEqual(hub_result["aggregated_metrics"]["monte_carlo"], mc_data)
        self.assertEqual(hub_result["aggregated_metrics"]["scenario"], scen_data)

        if callable(real_db_storage):
            stored_val = real_db_storage(action="get", key=dash_id)
            if stored_val is not None:
                self.assertEqual(stored_val.get("portfolio_id"), rand_portfolio_id)

if __name__ == "__main__":
    unittest.main()