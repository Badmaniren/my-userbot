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

    def test_stress_reporter_success_flow(self):
        storage = uuid.uuid4().hex
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        shifts = [round(random.uniform(-0.5, 0.5), 2), round(random.uniform(-0.5, 0.5), 2)]
        sim_data = {uuid.uuid4().hex: random.randint(100, 1000)}
        report_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as mock_gen_cls:

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.run_stress_test.return_value = sim_data

            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.generate_symbol_report.return_value = report_data

            reporter = StressReporter(storage)
            result = reporter.run_stress_reporting(symbol, shifts)

            mock_sim_instance.run_stress_test.assert_called_once_with(symbol, shifts)
            mock_gen_instance.generate_symbol_report.assert_called_once_with(symbol)
            self.assertEqual(result["simulation_results"], sim_data)
            self.assertEqual(result["base_report"], report_data)

    def test_stress_reporter_exception_handling(self):
        storage = uuid.uuid4().hex
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        shifts = [round(random.uniform(-0.2, 0.2), 2)]

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as mock_gen_cls:

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.run_stress_test.side_effect = Exception(uuid.uuid4().hex)

            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.generate_symbol_report.side_effect = Exception(uuid.uuid4().hex)

            reporter = StressReporter(storage)
            result = reporter.run_stress_reporting(symbol, shifts)

            self.assertEqual(result["simulation_results"], {})
            self.assertEqual(result["base_report"], {})

    def test_simulate_single_success(self):
        storage = uuid.uuid4().hex
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        percentage = round(random.uniform(-1.0, 1.0), 2)
        expected_output = {uuid.uuid4().hex: random.random()}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls:
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = expected_output

            reporter = StressReporter(storage)
            res = reporter.simulate_single(symbol, percentage)

            mock_sim_instance.simulate_scenario.assert_called_once_with(symbol, percentage)
            self.assertEqual(res, expected_output)

    def test_simulate_single_exception(self):
        storage = uuid.uuid4().hex
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        percentage = round(random.uniform(-1.0, 1.0), 2)

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls:
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.side_effect = Exception(uuid.uuid4().hex)

            reporter = StressReporter(storage)
            res = reporter.simulate_single(symbol, percentage)

            self.assertEqual(res, {})

    def test_get_stream_data_success(self):
        storage = uuid.uuid4().hex
        raw_stream = uuid.uuid4().hex.encode('utf-8')

        with patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as mock_gen_cls:
            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.get_raw_stream_dump.return_value = raw_stream

            reporter = StressReporter(storage)
            res = reporter.get_stream_data()

            mock_gen_instance.get_raw_stream_dump.assert_called_once()
            self.assertEqual(res, raw_stream)

    def test_get_stream_data_exception(self):
        storage = uuid.uuid4().hex

        with patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as mock_gen_cls:
            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.get_raw_stream_dump.side_effect = Exception(uuid.uuid4().hex)

            reporter = StressReporter(storage)
            res = reporter.get_stream_data()

            self.assertEqual(res, b"")

    def test_portfolio_stress_reporter_inheritance(self):
        storage = uuid.uuid4().hex
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        shifts = [round(random.uniform(-0.5, 0.5), 2)]
        expected = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(PortfolioStressReporter, "run_stress_reporting", return_value=expected) as mock_reporting:
            reporter = PortfolioStressReporter(storage)
            res = reporter.run_stress_report(symbol, shifts)

            mock_reporting.assert_called_once_with(symbol, shifts)
            self.assertEqual(res, expected)

    def test_generate_stress_report_helper(self):
        storage = uuid.uuid4().hex
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        percentage = round(random.uniform(-0.5, 0.5), 2)
        expected = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch.object(StressReporter, "run_stress_reporting", return_value=expected) as mock_run:
            res = generate_stress_report(storage, symbol, percentage)

            mock_run.assert_called_once_with(symbol, [percentage])
            self.assertEqual(res, expected)

    def test_run_stress_reporting_pipeline_helper(self):
        storage = uuid.uuid4().hex
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        shifts = [round(random.uniform(-0.5, 0.5), 2), round(random.uniform(-0.5, 0.5), 2)]
        expected = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(PortfolioStressReporter, "run_stress_report", return_value=expected) as mock_run:
            res = run_stress_reporting_pipeline(storage, symbol, shifts)

            mock_run.assert_called_once_with(symbol, shifts)
            self.assertEqual(res, expected)


if __name__ == "__main__":
    unittest.main()