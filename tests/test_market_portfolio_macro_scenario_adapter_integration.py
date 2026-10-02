import unittest
import uuid
import random
import os
from skills.market_portfolio_macro_scenario_adapter import (
    market_portfolio_macro_scenario_adapter,
    market_news_sentiment_analyzer,
    market_portfolio_scenario_simulator,
    db_storage
)

class TestMarketPortfolioMacroScenarioAdapterIntegration(unittest.TestCase):
    def test_macro_scenario_adapter_integration_flow(self):
        run_id = str(uuid.uuid4())
        mock_inflation = round(random.uniform(1.0, 15.0), 2)
        mock_rate = round(random.uniform(-0.5, 10.0), 2)

        sentiment_input = {
            "run_id": run_id,
            "metric": "inflation",
            "value": mock_inflation,
            "rate": mock_rate
        }

        sentiment_result = market_news_sentiment_analyzer(sentiment_input)
        self.assertIsNotNone(sentiment_result)

        scenario_payload = {
            "run_id": run_id,
            "sentiment_data": sentiment_result,
            "shock_multiplier": random.choice([1.2, 1.5, 2.0])
        }

        simulation_output = market_portfolio_scenario_simulator(scenario_payload)
        self.assertIn("scenario_id", simulation_output)

        adapter_payload = {
            "run_id": run_id,
            "simulation_result": simulation_output,
            "macro_factors": {
                "cpi": mock_inflation,
                "interest_rate": mock_rate
            }
        }

        adaptation_result = market_portfolio_macro_scenario_adapter(adapter_payload)

        self.assertEqual(adaptation_result.get("run_id"), run_id)
        self.assertTrue(adaptation_result.get("success", False))

        db_record = db_storage({"action": "get", "run_id": run_id})
        self.assertIsNotNone(db_record)
        self.assertEqual(db_record.get("run_id"), run_id)

        export_filename = f"macro_report_{run_id}.json"
        self.assertTrue(os.path.exists(export_filename) or adaptation_result.get("persisted", True))

        if os.path.exists(export_filename):
            os.remove(export_filename)

if __name__ == "__main__":
    unittest.main()