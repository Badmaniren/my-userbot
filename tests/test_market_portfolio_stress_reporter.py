import unittest
from unittest.mock import patch
import uuid
import random
import io

from skills.market_portfolio_stress_reporter import (
    StressReporter,
    PortfolioStressReporter,
    generate_stress_report,
    run_stress_reporting_pipeline
)


class TestMarketPortfolioStressReporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{random.randint(100, 999)}"
        self.shifts = [float(random.randint(-20, 20)), float(random.randint(-10, 10))]
        self.percentage = float(random.randint(1, 15))

    @patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_reporter.MarketReportGenerator")
    @patch("skills.market_portfolio_stress_reporter.PortfolioBacktestEvaluatorBridge")
    def test_run_stress_reporting_logic(self, mock_bridge_cls, mock_gen_cls, mock_sim_cls):
        mock_sim_instance = mock_sim_cls.return_value
        expected_sim_res = {"sim_id": uuid.uuid4().hex, "val": random.random()}
        mock_sim_instance.run_stress_test.return_value = expected_sim_res

        mock_gen_instance = mock_gen_cls.return_value
        expected_base_rep = {"report_id": uuid.uuid4().hex, "status": "ok"}
        mock_gen_instance.generate_symbol_report.return_value = expected_base_rep

        mock_bridge_instance = mock_bridge_cls.return_value
        expected_eval_res = {"eval_id": uuid.uuid4().hex, "score": random.randint(1, 100)}
        mock_bridge_instance.evaluate_retrospective.return_value = expected_eval_res

        reporter = StressReporter(self.storage_file)
        result = reporter.run_stress_reporting(self.symbol, self.shifts)

        mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
        mock_gen_instance.generate_symbol_report.assert_called_once_with(self.symbol)
        mock_bridge_instance.evaluate_retrospective.assert_called_once_with(self.symbol)

        self.assertEqual(result["simulation_results"], expected_sim_res)
        self.assertEqual(result["base_report"], expected_base_rep)
        self.assertEqual(result["retrospective_evaluation"], expected_eval_res)
        self.assertEqual(result["backtest_evaluation"], expected_eval_res)

    @patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator")
    def test_simulate_single(self, mock_sim_cls):
        mock_sim_instance = mock_sim_cls.return_value
        expected_single = {"scenario": uuid.uuid4().hex, "impact": random.random()}
        mock_sim_instance.simulate_scenario.return_value = expected_single

        reporter = StressReporter(self.storage_file)
        result = reporter.simulate_single(self.symbol, self.percentage)

        mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
        self.assertEqual(result, expected_single)

    @patch("skills.market_portfolio_stress_reporter.MarketReportGenerator")
    def test_get_stream_data(self, mock_gen_cls):
        mock_gen_instance = mock_gen_cls.return_value
        expected_stream = [uuid.uuid4().hex, uuid.uuid4().hex]
        mock_gen_instance.get_raw_stream_dump.return_value = expected_stream

        reporter = StressReporter(self.storage_file)
        result = reporter.get_stream_data()

        mock_gen_instance.get_raw_stream_dump.assert_called_once()
        self.assertEqual(result, expected_stream)

    @patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_reporter.MarketReportGenerator")
    @patch("skills.market_portfolio_stress_reporter.PortfolioBacktestEvaluatorBridge")
    def test_portfolio_stress_reporter_inheritance(self, mock_bridge_cls, mock_gen_cls, mock_sim_cls):
        mock_sim_instance = mock_sim_cls.return_value
        expected_sim_res = {"data": uuid.uuid4().hex}
        mock_sim_instance.run_stress_test.return_value = expected_sim_res

        mock_gen_instance = mock_gen_cls.return_value
        mock_gen_instance.generate_symbol_report.return_value = {}

        mock_bridge_instance = mock_bridge_cls.return_value
        mock_bridge_instance.evaluate_retrospective.return_value = {}

        reporter = PortfolioStressReporter(self.storage_file)
        result = reporter.run_stress_report(self.symbol, self.shifts)

        self.assertIn("simulation_results", result)
        self.assertEqual(result["simulation_results"], expected_sim_res)

    @patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_reporter.MarketReportGenerator")
    @patch("skills.market_portfolio_stress_reporter.PortfolioBacktestEvaluatorBridge")
    def test_generate_stress_report_helper(self, mock_bridge_cls, mock_gen_cls, mock_sim_cls):
        mock_sim_instance = mock_sim_cls.return_value
        expected_sim = {"id": uuid.uuid4().hex}
        mock_sim_instance.run_stress_test.return_value = expected_sim

        mock_gen_instance = mock_gen_cls.return_value
        mock_gen_instance.generate_symbol_report.return_value = {"rep": True}

        mock_bridge_instance = mock_bridge_cls.return_value
        mock_bridge_instance.evaluate_retrospective.return_value = {"eval": True}

        result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

        mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, [self.percentage])
        self.assertEqual(result["simulation_results"], expected_sim)

    @patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_reporter.MarketReportGenerator")
    @patch("skills.market_portfolio_stress_reporter.PortfolioBacktestEvaluatorBridge")
    def test_run_stress_reporting_pipeline_helper(self, mock_bridge_cls, mock_gen_cls, mock_sim_cls):
        mock_sim_instance = mock_sim_cls.return_value
        expected_sim = {"pipeline_id": uuid.uuid4().hex}
        mock_sim_instance.run_stress_test.return_value = expected_sim

        mock_gen_instance = mock_gen_cls.return_value
        mock_gen_instance.generate_symbol_report.return_value = {}

        mock_bridge_instance = mock_bridge_cls.return_value
        mock_bridge_instance.evaluate_retrospective.return_value = {}

        result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

        mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
        self.assertEqual(result["simulation_results"], expected_sim)

    def test_stream_data_io_mocking(self):
        random_bytes = uuid.uuid4().hex.encode('utf-8')
        mock_stream = io.BytesIO(random_bytes)

        with patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as mock_gen_cls:
            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.get_raw_stream_dump.return_value = mock_stream.read()

            reporter = StressReporter(self.storage_file)
            data = reporter.get_stream_data()
            self.assertEqual(data, random_bytes)


if __name__ == '__main__':
    unittest.main()