import unittest
from unittest.mock import patch
import json
import io
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import (
    PortfolioStressScenarioPipeline,
    run_stress_scenario_pipeline,
    market_portfolio_stress_scenario_pipeline
)


class TestPortfolioStressScenarioPipeline(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(-50.0, -5.0), 2)
        self.shifts = [round(random.uniform(-0.1, 0.1), 3) for _ in range(3)]

    def test_run_pipeline_payload_execution(self):
        pipeline = market_portfolio_stress_scenario_pipeline()
        payload = {
            "portfolio_id": "PF-TEST-123",
            "initial_capital": 500000.0,
            "assets": [
                {"ticker": "AAPL", "weight": 0.6, "current_price": 150.0},
                {"ticker": "GOOGL", "weight": 0.4, "current_price": 2800.0}
            ],
            "scenarios": [
                {
                    "scenario_id": "MARKET_CRASH",
                    "description": "30% market crash",
                    "shocks": {"AAPL": -0.30, "GOOGL": -0.25},
                    "volatility_multiplier": 2.5
                }
            ]
        }
        output = pipeline.run_pipeline(payload)
        self.assertEqual(output["execution_status"], "SUCCESS")
        self.assertEqual(output["portfolio_id"], "PF-TEST-123")
        self.assertEqual(len(output["scenario_results"]), 1)
        res = output["scenario_results"][0]
        self.assertEqual(res["scenario_id"], "MARKET_CRASH")
        self.assertIn("shocked_portfolio_value", res)
        self.assertIn("pnl", res)

    def test_pipeline_class_execution(self):
        sim_val = round(random.uniform(10.0, 1000.0), 2)
        stress_res = [round(random.uniform(-5.0, 5.0), 2) for _ in range(2)]
        rep_res = {"status": uuid.uuid4().hex, "score": random.randint(1, 100)}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as mock_rep_cls:

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = {"symbol": self.symbol, "val": sim_val}
            mock_sim_instance.run_stress_test.return_value = stress_res

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_report.return_value = rep_res

            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            result = pipeline.execute(self.symbol, self.percentage, self.shifts)

            self.assertIn("simulation", result)
            self.assertIn("stress_test", result)
            self.assertIn("stress_report", result)
            self.assertEqual(result["simulation"]["val"], sim_val)
            self.assertEqual(result["stress_test"], stress_res)
            self.assertEqual(result["stress_report"], rep_res)

    def test_run_stress_scenario_pipeline_success(self):
        sim_val = round(random.uniform(50.0, 500.0), 2)
        stress_results_list = [round(random.uniform(-10.0, 10.0), 2), round(random.uniform(-10.0, 10.0), 2)]
        report_impact = random.randint(10, 99)

        valid_json_data = json.dumps({uuid.uuid4().hex: random.randint(1, 100)})

        with patch("builtins.open", create=True) as mock_open, \
             patch("json.loads") as mock_json_loads, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:

            mock_open.return_value.__enter__.return_value.read.return_value = valid_json_data
            mock_json_loads.return_value = {uuid.uuid4().hex: uuid.uuid4().hex}

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = {"symbol": self.symbol, "simulated_value": sim_val}
            mock_sim_instance.run_stress_test.return_value = stress_results_list

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.return_value = {"symbol": self.symbol, "impact_score": report_impact}

            res = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertIsInstance(res, dict)
            self.assertEqual(res["simulation"]["simulated_value"], sim_val)
            self.assertEqual(res["stress_test"]["results"], stress_results_list)
            self.assertEqual(res["stress_report"]["impact_score"], report_impact)

    def test_run_stress_scenario_pipeline_invalid_storage_recovers(self):
        sim_val = round(random.uniform(1.0, 50.0), 2)

        with patch("builtins.open", create=True) as mock_open, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:

            file_mock = mock_open.return_value.__enter__.return_value
            file_mock.read.side_effect = json.JSONDecodeError("Expecting value", "", 0)

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = {"symbol": self.symbol, "simulated_value": sim_val}
            mock_sim_instance.run_stress_test.side_effect = KeyError("Missing shift")

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.side_effect = Exception("Reporting failure")

            res = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertIn("simulation", res)
            self.assertIn("stress_test", res)
            self.assertIn("stress_report", res)
            self.assertEqual(res["simulation"]["simulated_value"], sim_val)
            self.assertEqual(res["stress_test"]["results"], [])
            self.assertEqual(res["stress_report"]["status"], "default")

    def test_run_stress_scenario_pipeline_keyerror_handling(self):
        with patch("builtins.open", create=True) as mock_open, \
             patch("json.loads") as mock_json_loads, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:

            mock_open.return_value.__enter__.return_value.read.return_value = "{}"
            mock_json_loads.return_value = {}

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.side_effect = KeyError("Symbol not found")
            mock_sim_instance.run_stress_test.side_effect = KeyError("Shift not found")

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.return_value = {"symbol": self.symbol, "status": "ok"}

            res = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(res["simulation"]["simulated_value"], 0.0)
            self.assertEqual(res["stress_test"]["results"], [])
            self.assertEqual(res["stress_report"]["status"], "ok")
