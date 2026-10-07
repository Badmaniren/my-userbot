import unittest
import uuid
import os
import json
from skills import db_storage
import skills.market_portfolio_collector_agent as market_portfolio_collector_agent
import skills.market_portfolio_stress_monte_carlo_engine as market_portfolio_stress_monte_carlo_engine
import skills.market_portfolio_stress_scenario_pipeline as market_portfolio_stress_scenario_pipeline
import skills.market_portfolio_stress_reporter as market_portfolio_stress_reporter
import skills.market_portfolio_var_liquidity_core as market_portfolio_var_liquidity_core
import skills.market_portfolio_stress_scenario_matrix_evaluator as market_portfolio_stress_scenario_matrix_evaluator
import skills.market_portfolio_audit_log_exporter as market_portfolio_audit_log_exporter
import skills.market_portfolio_stress_auto_rebalance_trigger as market_portfolio_stress_auto_rebalance_trigger
from skills.market_portfolio_stress_testing_unified_hub import (
    MarketPortfolioStressTestingUnifiedHub,
    market_portfolio_stress_testing_unified_hub
)

class TestMarketPortfolioStressTestingUnifiedHubIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.iterations = int(uuid.uuid4().int % 1000 + 100)
        self.scenario_code = f"SCENARIO_{uuid.uuid4().hex[:8].upper()}"
        self.output_file = f"test_report_{uuid.uuid4().hex}.json"

        self.hub = MarketPortfolioStressTestingUnifiedHub(
            db_storage=db_storage,
            market_portfolio_stress_monte_carlo_engine=market_portfolio_stress_monte_carlo_engine,
            market_portfolio_stress_scenario_pipeline=market_portfolio_stress_scenario_pipeline,
            market_portfolio_stress_reporter=market_portfolio_stress_reporter,
            market_portfolio_var_liquidity_core=market_portfolio_var_liquidity_core,
            market_portfolio_stress_scenario_matrix_evaluator=market_portfolio_stress_scenario_matrix_evaluator,
            market_portfolio_audit_log_exporter=market_portfolio_audit_log_exporter,
            market_portfolio_stress_auto_rebalance_trigger=market_portfolio_stress_auto_rebalance_trigger
        )

    def tearDown(self):
        if os.path.exists(self.output_file):
            try:
                os.remove(self.output_file)
            except OSError:
                pass

    def test_execute_stress_testing_pipeline_integration(self):
        result = self.hub.execute_stress_testing_pipeline(
            portfolio_id=self.portfolio_id,
            iterations=self.iterations,
            scenario_code=self.scenario_code
        )
        self.assertIn("monte_carlo", result)
        self.assertIn("scenario", result)
        self.assertIn("report_id", result)
        self.assertIsNotNone(result["report_id"])

    def test_market_portfolio_stress_testing_unified_hub_functional_wrapper(self):
        monte_carlo_val = float(uuid.uuid4().int % 10000) / 100.0
        scenarios_val = f"data_{uuid.uuid4().hex}"

        payload = {
            "portfolio_id": self.portfolio_id,
            "output_file": self.output_file,
            "monte_carlo": monte_carlo_val,
            "scenarios": scenarios_val
        }

        response = market_portfolio_stress_testing_unified_hub(payload)

        self.assertEqual(response["portfolio_id"], self.portfolio_id)
        self.assertTrue(response["success"])
        self.assertEqual(response["monte_carlo"], monte_carlo_val)
        self.assertEqual(response["scenarios"], scenarios_val)
        self.assertEqual(response["output_file"], self.output_file)

        self.assertTrue(os.path.exists(self.output_file))
        with open(self.output_file, "r", encoding="utf-8") as f:
            file_data = json.load(f)
            self.assertEqual(file_data["portfolio_id"], self.portfolio_id)
            self.assertEqual(file_data["monte_carlo"], monte_carlo_val)
            self.assertEqual(file_data["scenarios"], scenarios_val)

if __name__ == "__main__":
    unittest.main()
