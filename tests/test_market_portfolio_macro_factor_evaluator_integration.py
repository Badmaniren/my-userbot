import unittest
import uuid
import random
import os
import json
from datetime import datetime

from skills.market_portfolio_macro_factor_evaluator import evaluate_macro_factors_realtime
from skills.db_storage import save_macro_evaluation, get_macro_evaluation
from skills.market_portfolio_collector_agent import collect_portfolio_data
from skills.market_parser import parse_macro_indicators
from skills.market_portfolio_alert_dispatcher import dispatch_macro_alert

class TestMarketPortfolioMacroFactorEvaluatorIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.test_user_id = random.randint(10000, 99999)
        self.inflation_rate = round(random.uniform(1.0, 15.0), 2)
        self.interest_rate = round(random.uniform(0.0, 10.0), 2)
        self.usd_rate = round(random.uniform(70.0, 100.0), 2)
        self.output_file_path = f"macro_eval_{self.portfolio_id}.json"

    def tearDown(self):
        if os.path.exists(self.output_file_path):
            os.remove(self.output_file_path)

    def test_realtime_macro_factor_evaluation_integration(self):
        raw_market_data = parse_macro_indicators({
            "inflation": self.inflation_rate,
            "interest_rate": self.interest_rate,
            "usd_rub": self.usd_rate,
            "timestamp": datetime.utcnow().isoformat()
        })

        self.assertIsNotNone(raw_market_data)

        portfolio_payload = collect_portfolio_data(
            portfolio_id=self.portfolio_id,
            user_id=self.test_user_id
        )

        self.assertEqual(portfolio_payload["portfolio_id"], self.portfolio_id)

        evaluation_result = evaluate_macro_factors_realtime(
            portfolio=portfolio_payload,
            macro_indicators=raw_market_data
        )

        self.assertIn("impact_score", evaluation_result)
        self.assertIn("risk_level", evaluation_result)

        evaluation_id = str(uuid.uuid4())
        evaluation_result["evaluation_id"] = evaluation_id
        evaluation_result["portfolio_id"] = self.portfolio_id

        save_macro_evaluation(evaluation_result)

        persisted_data = get_macro_evaluation(evaluation_id)
        self.assertIsNotNone(persisted_data)
        self.assertEqual(persisted_data["evaluation_id"], evaluation_id)
        self.assertEqual(persisted_data["portfolio_id"], self.portfolio_id)

        with open(self.output_file_path, "w", encoding="utf-8") as f:
            json.dump(persisted_data, f)

        self.assertTrue(os.path.exists(self.output_file_path), "Файл с результатами оценки макрофакторов не был создан")

        alert_dispatch_status = dispatch_macro_alert(
            portfolio_id=self.portfolio_id,
            risk_level=evaluation_result["risk_level"]
        )
        self.assertTrue(alert_dispatch_status)

if __name__ == "__main__":
    unittest.main()