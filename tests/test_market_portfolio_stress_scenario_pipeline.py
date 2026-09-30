import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import json
from skills.market_portfolio_stress_scenario_pipeline import (
    PortfolioStressScenarioPipeline,
    run_stress_scenario_pipeline,
)


class TestPortfolioStressScenarioPipelineStrict(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(random.randint(1, 3))]

    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter")
    def test_pipeline_class_execution_success(self, mock_reporter_cls, mock_simulator_cls):
        sim_instance = mock_simulator_cls.return_value
        rep_instance = mock_reporter_cls.return_value

        expected_sim = {"sim": uuid.uuid4().hex}
        expected_test = {"test": uuid.uuid4().hex}
        expected_report = {"report": uuid.uuid4().hex}

        sim_instance.simulate_scenario.return_value = expected_sim
        sim_instance.run_stress_test.return_value = expected_test
        rep_instance.run_stress_report.return_value = expected_report

        pipeline = PortfolioStressScenarioPipeline(self.storage_file)
        result = pipeline.execute(self.symbol, self.percentage, self.shifts)

        sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
        sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
        rep_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)

        self.assertEqual(result["simulation"], expected_sim)
        self.assertEqual(result["stress_test"], expected_test)
        self.assertEqual(result["stress_report"], expected_report)

    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter")
    def test_pipeline_class_propagates_exceptions(self, mock_reporter_cls, mock_simulator_cls):
        sim_instance = mock_simulator_cls.return_value
        error_msg = f"ERR_{uuid.uuid4().hex}"
        sim_instance.simulate_scenario.side_effect = RuntimeError(error_msg)

        pipeline = PortfolioStressScenarioPipeline(self.storage_file)
        with self.assertRaises(RuntimeError) as ctx:
            pipeline.execute(self.symbol, self.percentage, self.shifts)

        self.assertIn(error_msg, str(ctx.exception))

    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter")
    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator")
    def test_functional_pipeline_file_initialization_and_exceptions(self, mock_simulator_cls, mock_reporter_cls):
        sim_instance = mock_simulator_cls.return_value
        error_msg = f"Missing symbol {uuid.uuid4().hex}"
        sim_instance.simulate_scenario.side_effect = KeyError(error_msg)

        with self.assertRaises(KeyError) as ctx:
            run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

        self.assertIn(error_msg, str(ctx.exception))

    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter")
    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator")
    def test_functional_pipeline_successful_flow(self, mock_simulator_cls, mock_reporter_cls):
        sim_instance = mock_simulator_cls.return_value
        rep_instance = mock_reporter_cls.return_value

        valid_content = json.dumps({uuid.uuid4().hex: random.randint(100, 500)})

        sim_result_raw = {"val": uuid.uuid4().hex}
        stress_test_list = [random.uniform(1.0, 10.0), random.uniform(11.0, 20.0)]
        report_result = {"status": "ok", "score": random.randint(1, 10)}

        sim_instance.simulate_scenario.return_value = sim_result_raw
        sim_instance.run_stress_test.return_value = stress_test_list
        rep_instance.run_stress_report.return_value = report_result

        with patch("builtins.open", mock_open(read_data=valid_content)):
            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"], sim_result_raw)
            self.assertEqual(result["stress_test"], stress_test_list)
            self.assertEqual(result["stress_report"], report_result)

    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter")
    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator")
    def test_functional_pipeline_file_not_found(self, mock_simulator_cls, mock_reporter_cls):
        sim_instance = mock_simulator_cls.return_value
        sim_instance.simulate_scenario.return_value = {"status": "simulated"}
        sim_instance.run_stress_test.return_value = {"status": "tested"}

        rep_instance = mock_reporter_cls.return_value
        rep_instance.run_stress_report.return_value = {"status": "reported"}

        m_open = mock_open()
        m_open.side_effect = [FileNotFoundError, m_open.return_value]

        with patch("builtins.open", m_open):
            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)
            self.assertIn("simulation", result)
            self.assertIn("stress_test", result)
            self.assertIn("stress_report", result)


if __name__ == "__main__":
    unittest.main()
