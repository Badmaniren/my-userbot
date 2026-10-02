import unittest
from unittest.mock import patch
import uuid
import random
from skills.market_portfolio_stress_reporter import (
    StressReporter,
    PortfolioStressReporter,
    generate_stress_report,
    run_stress_reporting_pipeline
)

class TestMarketPortfolioStressReporter(unittest.TestCase):

    def test_stress_reporter_initialization_and_pipeline(self):
        storage = f"storage_{uuid.uuid4().hex}.db"
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        shifts = [random.uniform(-0.5, 0.5) for _ in range(random.randint(1, 3))]
        sim_data = {f"shift_{uuid.uuid4().hex[:4]}": random.randint(100, 500)}
        report_data = {"base": uuid.uuid4().hex}
        stream_data = [uuid.uuid4().hex, uuid.uuid4().hex]

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as mock_gen_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.run_stress_test.return_value = sim_data

            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.generate_symbol_report.return_value = report_data
            mock_gen_instance.get_raw_stream_dump.return_value = stream_data

            reporter = StressReporter(storage)
            result = reporter.run_stress_reporting(symbol, shifts)

            self.assertEqual(result["simulation_results"], sim_data)
            self.assertEqual(result["base_report"], report_data)
            self.assertIn(symbol, result["compact_text_report"])
            self.assertEqual(result["tabular_report"][0]["symbol"], symbol)
            self.assertEqual(result["tabular_report"][0]["shifts"], shifts)
            self.assertEqual(result["tabular_report"][0]["results"], sim_data)
            self.assertEqual(result["chart_export"]["data"], sim_data)

            stream_dump = reporter.get_stream_data()
            self.assertEqual(stream_dump, stream_data)

    def test_simulate_single_success_and_key_error(self):
        storage = f"storage_{uuid.uuid4().hex}.db"
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        percentage = random.uniform(-0.2, 0.2)
        expected_res = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator"):
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = expected_res

            reporter = StressReporter(storage)
            res = reporter.simulate_single(symbol, percentage)
            self.assertEqual(res, expected_res)

            mock_sim_instance.simulate_scenario.side_effect = KeyError("Missing symbol")
            res_error = reporter.simulate_single(symbol, percentage)
            self.assertEqual(res_error, {})

    def test_portfolio_stress_reporter_inheritance(self):
        storage = f"storage_{uuid.uuid4().hex}.db"
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        shifts = [random.uniform(-0.1, 0.1)]
        expected_output = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator"), \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator"), \
             patch.object(StressReporter, "run_stress_reporting", return_value=expected_output) as mock_run:
            
            portfolio_reporter = PortfolioStressReporter(storage)
            res = portfolio_reporter.run_stress_report(symbol, shifts)

            mock_run.assert_called_once_with(symbol, shifts)
            self.assertEqual(res, expected_output)

    def test_generate_stress_report_helper(self):
        storage = f"storage_{uuid.uuid4().hex}.db"
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        percentage = random.uniform(-0.3, 0.3)
        expected_output = {uuid.uuid4().hex: random.randint(10, 50)}

        with patch.object(StressReporter, "run_stress_reporting", return_value=expected_output) as mock_run:
            res = generate_stress_report(storage, symbol, percentage)
            mock_run.assert_called_once_with(symbol, [percentage])
            self.assertEqual(res, expected_output)

    def test_run_stress_reporting_pipeline_helper(self):
        storage = f"storage_{uuid.uuid4().hex}.db"
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        shifts = [random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4)]
        expected_output = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(PortfolioStressReporter, "run_stress_report", return_value=expected_output) as mock_run:
            res = run_stress_reporting_pipeline(storage, symbol, shifts)
            mock_run.assert_called_once_with(symbol, shifts)
            self.assertEqual(res, expected_output)

if __name__ == "__main__":
    unittest.main()