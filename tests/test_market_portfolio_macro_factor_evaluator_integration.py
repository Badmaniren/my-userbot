import unittest
import uuid
import random
from skills.market_portfolio_macro_factor_evaluator import start_new, evaluate_macro_factors
from skills.db_storage import save_record, get_record
from skills.market_portfolio_integration_hub import process_integration_payload

class TestMarketPortfolioMacroFactorEvaluatorIntegration(unittest.TestCase):

    def test_macro_factor_evaluation_pipeline_integration(self):
        random_target_id = str(uuid.uuid4())
        random_portfolio_id = f"port_{uuid.uuid4().hex[:6]}"

        indicators_pool = ["inflation_rate", "interest_rate", "gdp_growth", "unemployment", "sp500_index"]
        selected_indicators = random.sample(indicators_pool, k=random.randint(1, 3))

        payload = {
            "target_id": random_target_id,
            "indicators": selected_indicators
        }

        start_result = start_new(payload)

        self.assertIn("evaluated_factor", start_result)
        self.assertIn("token", start_result)

        eval_result = evaluate_macro_factors(random_portfolio_id, selected_indicators)

        self.assertIn("evaluation_id", eval_result)
        self.assertEqual(eval_result["portfolio_id"], random_portfolio_id)
        self.assertEqual(eval_result["indicators"], selected_indicators)

        storage_key = f"macro_eval_{eval_result['evaluation_id']}"
        save_record(storage_key, eval_result)

        retrieved_record = get_record(storage_key)
        self.assertIsNotNone(retrieved_record)
        self.assertEqual(retrieved_record.get("portfolio_id"), random_portfolio_id)
        self.assertEqual(retrieved_record.get("indicators"), selected_indicators)

        integration_payload = {
            "event": "macro_factor_evaluated",
            "evaluation_id": eval_result["evaluation_id"],
            "portfolio_id": random_portfolio_id,
            "factor_token": start_result["token"]
        }

        integration_response = process_integration_payload(integration_payload)
        self.assertIsNotNone(integration_response)

if __name__ == "__main__":
    unittest.main()