import unittest
from unittest.mock import patch, MagicMock
import json
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import (
    PortfolioStressScenarioPipeline,
    run_stress_scenario_pipeline,
    execute_stress_test
)

class TestPortfolioStressScenarioPipeline(unittest.TestCase):
    def setUp(self):
        self.random_storage = f"{uuid.uuid4().hex}.json"
        self.random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_percentage = round(random.uniform(1.0, 50.0), 2)
        self.random_shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]

    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter")
    def test_pipeline_class_execution(self, mock_reporter_cls, mock_simulator_cls):
        mock_simulator = mock_simulator_cls.return_value
        mock_reporter = mock_reporter_cls.return_value

        expected_sim = {"symbol": self.random_symbol, "val": random.randint(100, 1000)}
        expected_test = [{"shift": s, "val": random.randint(50, 500)} for s in self.random_shifts]
        expected_report = {"report_id": uuid.uuid4().hex, "status": "ok"}

        mock_simulator.simulate_scenario.return_value = expected_sim
        mock_simulator.run_stress_test.return_value = expected_test
        mock_reporter.run_stress_report.return_value = expected_report

        pipeline = PortfolioStressScenarioPipeline(self.random_storage)
        result = pipeline.execute(self.random_symbol, self.random_percentage, self.random_shifts)

        mock_simulator.simulate_scenario.assert_called_once_with(self.random_symbol, self.random_percentage)
        mock_simulator.run_stress_test.assert_called_once_with(self.random_symbol, self.random_shifts)
        mock_reporter.run_stress_report.assert_called_once_with(self.random_symbol, self.random_shifts)

        self.assertEqual(result["simulation"], expected_sim)
        self.assertEqual(result["stress_test"], expected_test)
        self.assertEqual(result["stress_report"], expected_report)

    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter")
    def test_run_stress_scenario_pipeline(self, mock_reporter_cls, mock_simulator_cls):
        mock_simulator = mock_simulator_cls.return_value
        mock_reporter = mock_reporter_cls.return_value

        expected_sim = {"sim": uuid.uuid4().hex}
        expected_test = [{"shift": 1.0, "valuation": 100}]
        expected_report = {"report": uuid.uuid4().hex}

        mock_simulator.simulate_scenario.return_value = expected_sim
        mock_simulator.run_stress_test.return_value = expected_test
        mock_reporter.run_stress_report.return_value = expected_report

        res = run_stress_scenario_pipeline(self.random_storage, self.random_symbol, self.random_percentage, self.random_shifts)

        self.assertEqual(res["simulation"], expected_sim)
        self.assertEqual(res["stress_test"], expected_test)
        self.assertEqual(res["stress_report"], expected_report)

    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter")
    def test_execute_stress_test_payload(self, mock_reporter_cls, mock_simulator_cls):
        mock_simulator = mock_simulator_cls.return_value
        mock_reporter = mock_reporter_cls.return_value

        expected_sim = {"sim": "ok"}
        expected_test = []
        expected_report = {"report": "ok"}

        mock_simulator.simulate_scenario.return_value = expected_sim
        mock_simulator.run_stress_test.return_value = expected_test
        mock_reporter.run_stress_report.return_value = expected_report

        payload = {
            "storage_file": self.random_storage,
            "symbol": self.random_symbol,
            "percentage": self.random_percentage,
            "shifts": self.random_shifts
        }

        res = execute_stress_test(payload)

        self.assertEqual(res["simulation"], expected_sim)
        self.assertEqual(res["stress_test"], expected_test)
        self.assertEqual(res["stress_report"], expected_report)

    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator")
    def test_honest_exception_propagation(self, mock_simulator_cls):
        mock_simulator = mock_simulator_cls.return_value
        mock_simulator.simulate_scenario.side_effect = KeyError(f"Symbol {self.random_symbol} not found")

        pipeline = PortfolioStressScenarioPipeline(self.random_storage)
        with self.assertRaises(KeyError):
            pipeline.execute(self.random_symbol, self.random_percentage, self.random_shifts)

if __name__ == "__main__":
    unittest.main()
