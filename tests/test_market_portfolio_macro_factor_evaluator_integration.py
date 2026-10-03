import unittest
import uuid
import random
import os
from skills.market_portfolio_macro_factor_evaluator import market_portfolio_macro_factor_evaluator
from skills.market_portfolio_liquidity_scenario_analyzer import market_portfolio_liquidity_scenario_analyzer
from skills.market_portfolio_stress_scenario_pipeline import market_portfolio_stress_scenario_pipeline
from skills.db_storage import db_storage

class TestMarketPortfolioMacroFactorEvaluatorIntegration(unittest.TestCase):
    def test_macro_factor_evaluator_integration_flow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        risk_threshold = round(random.uniform(0.01, 0.99), 4)
        liquidity_shock = round(random.uniform(1000.0, 1000000.0), 2)
        
        liquidity_data = market_portfolio_liquidity_scenario_analyzer({
            "portfolio_id": portfolio_id,
            "shock_value": liquidity_shock
        })
        
        self.assertIsInstance(liquidity_data, dict)
        
        stress_pipeline_result = market_portfolio_stress_scenario_pipeline({
            "portfolio_id": portfolio_id,
            "liquidity_metrics": liquidity_data,
            "threshold": risk_threshold
        })
        
        self.assertIsInstance(stress_pipeline_result, dict)
        
        evaluation_payload = {
            "evaluation_id": f"eval_{uuid.uuid4().hex}",
            "portfolio_id": portfolio_id,
            "risk_threshold": risk_threshold,
            "liquidity_scenario": liquidity_data,
            "stress_pipeline": stress_pipeline_result
        }
        
        eval_result = market_portfolio_macro_factor_evaluator(evaluation_payload)
        
        self.assertIsInstance(eval_result, dict)
        self.assertIn("status", eval_result)
        self.assertEqual(eval_result.get("portfolio_id"), portfolio_id)
        
        db_storage({
            "action": "save_macro_evaluation",
            "data": eval_result
        })
        
        db_record = db_storage({
            "action": "get_macro_evaluation",
            "evaluation_id": evaluation_payload["evaluation_id"]
        })
        
        self.assertIsNotNone(db_record)
        self.assertEqual(db_record.get("evaluation_id"), evaluation_payload["evaluation_id"])

if __name__ == "__main__":
    unittest.main()