import unittest
from unittest.mock import patch, mock_open
import io
import json
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import (
    PortfolioStressScenarioPipeline,
    run_stress_scenario_pipeline
)

class TestMarketPortfolioStressScenarioPipeline(unittest.TestCase):

    def test_pipeline_class_execution(self):
        storage_filename = f"{uuid.uuid4().hex}.json"
        symbol_name = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        percentage_val = round(random.uniform(-50.0, 50.0), 2)
        shifts_list = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]

        sim_out = {f"sim_{uuid.uuid4().hex[:4]}": random.randint(100, 999)}
        stress_out = {f"stress_{uuid.uuid4().hex[:4]}": random.randint(100, 999)}
        report_out = {f"report_{uuid.uuid4().hex[:4]}": random.randint(100, 999)}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as mock_rep_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = sim_out
            mock_sim_instance.run_stress_test.return_value = stress_out

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_report.return_value = report_out

            pipeline = PortfolioStressScenarioPipeline(storage_filename)
            result = pipeline.execute(symbol_name, percentage_val, shifts_list)

            mock_sim_cls.assert_called_once_with(storage_filename)
            mock_rep_cls.assert_called_once_with(storage_filename)
            mock_sim_instance.simulate_scenario.assert_called_once_with(symbol_name, percentage_val)
            mock_sim_instance.run_stress_test.assert_called_once_with(symbol_name, shifts_list)
            mock_rep_instance.run_stress_report.assert_called_once_with(symbol_name, shifts_list)

            self.assertEqual(result["simulation"], sim_out)
            self.assertEqual(result["stress_test"], stress_out)
            self.assertEqual(result["stress_report"], report_out)

    def test_functional_pipeline_success(self):
        storage_filename = f"{uuid.uuid4().hex}.json"
        symbol_name = f"TICK_{uuid.uuid4().hex[:5].upper()}"
        percentage_val = round(random.uniform(1.0, 25.0), 2)
        shifts_list = [round(random.uniform(-5.0, 5.0), 2), round(random.uniform(-5.0, 5.0), 2)]

        valid_data = {uuid.uuid4().hex: random.randint(1, 100)}
        json_bytes = json.dumps(valid_data).encode("utf-8")

        sim_res = {f"sim_val_{uuid.uuid4().hex[:4]}": random.random()}
        stress_res = [f"res_{uuid.uuid4().hex[:4]}"]
        report_res = {f"rep_val_{uuid.uuid4().hex[:4]}": random.randint(10, 50)}

        mock_file = io.BytesIO(json_bytes)

        with patch("builtins.open", side_effect=lambda *args, **kwargs: mock_file if "r" in args[1] else mock_open()(*args, **kwargs)), \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:

            sim_instance = mock_sim_cls.return_value
            sim_instance.simulate_scenario.return_value = sim_res
            sim_instance.run_stress_test.return_value = stress_res

            rep_instance = mock_rep_cls.return_value
            rep_instance.run_stress_reporting.return_value = report_res

            result = run_stress_scenario_pipeline(storage_filename, symbol_name, percentage_val, shifts_list)

            self.assertEqual(result["simulation"], sim_res)
            self.assertEqual(result["stress_test"]["symbol"], symbol_name)
            self.assertEqual(result["stress_test"]["shifts"], shifts_list)
            self.assertEqual(result["stress_test"]["results"], stress_res)
            self.assertEqual(result["stress_report"], report_res)

    def test_functional_pipeline_corrupted_storage(self):
        storage_filename = f"{uuid.uuid4().hex}.json"
        symbol_name = f"ERR_{uuid.uuid4().hex[:4].upper()}"
        percentage_val = round(random.uniform(-10.0, 0.0), 2)
        shifts_list = [1.0, 2.0]

        garbage_content = b"\xe7\xff\xfeinvalid_bytes"
        mock_file = io.BytesIO(garbage_content)

        with patch("builtins.open", side_effect=lambda *args, **kwargs: mock_file if "r" in args[1] else mock_open()(*args, **kwargs)), \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:

            sim_instance = mock_sim_cls.return_value
            sim_instance.simulate_scenario.side_effect = KeyError("missing")
            sim_instance.run_stress_test.side_effect = KeyError("missing")

            rep_instance = mock_rep_cls.return_value
            rep_instance.run_stress_reporting.side_effect = Exception("fail")

            result = run_stress_scenario_pipeline(storage_filename, symbol_name, percentage_val, shifts_list)

            self.assertEqual(result["simulation"], {"symbol": symbol_name, "percentage": percentage_val, "simulated_value": 0.0})
            self.assertEqual(result["stress_test"], {"symbol": symbol_name, "shifts": shifts_list, "results": []})
            self.assertEqual(result["stress_report"], {"symbol": symbol_name, "status": "default", "impact_score": 0})