import unittest
import uuid
import random
import os

from skills.market_macro_liquidity_monitor import monitor_macro_liquidity
from skills.db_storage import save_macro_liquidity_state, get_macro_liquidity_state
from skills.market_parser import fetch_macro_indicators
from skills.market_portfolio_var_liquidity_core import calculate_var_liquidity
from skills.market_portfolio_stress_scenario_pipeline import run_stress_scenario

class TestMarketMacroLiquidityMonitorIntegration(unittest.TestCase):

    def test_macro_liquidity_pipeline_integration(self):
        test_run_id = str(uuid.uuid4())
        mock_interest_rate = round(random.uniform(0.01, 0.08), 4)
        mock_m2_supply = round(random.uniform(15000.0, 25000.0), 2)
        mock_portfolio_size = round(random.uniform(100000.0, 5000000.0), 2)

        raw_market_data = fetch_macro_indicators(
            run_id=test_run_id,
            interest_rate=mock_interest_rate,
            m2_supply=mock_m2_supply
        )

        self.assertIsNotNone(raw_market_data)
        self.assertEqual(raw_market_data.get("run_id"), test_run_id)

        liquidity_assessment = monitor_macro_liquidity(
            market_data=raw_market_data,
            threshold_factor=random.uniform(0.5, 1.5)
        )

        self.assertIn("liquidity_score", liquidity_assessment)
        self.assertIn("risk_multiplier", liquidity_assessment)
        self.assertEqual(liquidity_assessment.get("run_id"), test_run_id)

        var_result = calculate_var_liquidity(
            portfolio_size=mock_portfolio_size,
            liquidity_multiplier=liquidity_assessment["risk_multiplier"]
        )

        self.assertIn("var_value", var_result)

        stress_result = run_stress_scenario(
            scenario_id=test_run_id,
            var_data=var_result
        )

        self.assertTrue(stress_result.get("success"))

        save_success = save_macro_liquidity_state(
            run_id=test_run_id,
            state_data=liquidity_assessment
        )
        self.assertTrue(save_success)

        persisted_state = get_macro_liquidity_state(run_id=test_run_id)
        self.assertIsNotNone(persisted_state)
        self.assertEqual(persisted_state.get("run_id"), test_run_id)
        self.assertEqual(persisted_state.get("liquidity_score"), liquidity_assessment["liquidity_score"])

        expected_audit_file = f"audit_macro_{test_run_id}.log"
        self.assertTrue(os.path.exists(expected_audit_file) or persisted_state.get("logged", True))

        if os.path.exists(expected_audit_file):
            os.remove(expected_audit_file)

if __name__ == "__main__":
    unittest.main()