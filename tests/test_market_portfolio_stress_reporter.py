import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_portfolio_stress_reporter import (
    StressReporter,
    PortfolioStressReporter,
    generate_stress_report,
    run_stress_reporting_pipeline
)


class TestStressReporter(unittest.TestCase):

    def test_run_stress_reporting_success(self):
        storage_file = f"{uuid.uuid4().hex}.db"
        symbol = f"SYM_{random.randint(1000, 9999)}"
        shifts = [random.uniform(-0.5, 0.5) for _ in range(random.randint(2, 5))]
        
        sim_mock_data = {uuid.uuid4().hex: random.random()}
        report_mock_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSimulator, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGenerator:
            
            sim_instance = MockSimulator.return_value
            sim_instance.run_stress_test.return_value = sim_mock_data

            gen_instance = MockGenerator.return_value
            gen_instance.generate_symbol_report.return_value = report_mock_data

            reporter = StressReporter(storage_file)
            result = reporter.run_stress_reporting(symbol, shifts)

            MockSimulator.assert_called_once_with(storage_file)
            MockGenerator.assert_called_once_with(storage_file)
            sim_instance.run_stress_test.assert_called_once_with(symbol, shifts)
            gen_instance.generate_symbol_report.assert_called_once_with(symbol)

            self.assertIn("simulation_results", result)
            self.assertIn("base_report", result)
            self.assertEqual(result["simulation_results"], sim_mock_data)
            self.assertEqual(result["base_report"], report_mock_data)

    def test_simulate_single_success(self):
        storage_file = f"{uuid.uuid4().hex}.db"
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        percentage = random.uniform(-0.2, 0.2)
        expected_result = {uuid.uuid4().hex: random.random()}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSimulator, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator'):
            
            sim_instance = MockSimulator.return_value
            sim_instance.simulate_scenario.return_value = expected_result

            reporter = StressReporter(storage_file)
            result = reporter.simulate_single(symbol, percentage)

            sim_instance.simulate_scenario.assert_called_once_with(symbol, percentage)
            self.assertEqual(result, expected_result)

    def test_simulate_single_key_error(self):
        storage_file = f"{uuid.uuid4().hex}.db"
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        percentage = random.uniform(-0.2, 0.2)

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSimulator, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator'):
            
            sim_instance = MockSimulator.return_value
            sim_instance.simulate_scenario.side_effect = KeyError

            reporter = StressReporter(storage_file)
            result = reporter.simulate_single(symbol, percentage)

            self.assertEqual(result, {})

    def test_get_stream_data(self):
        storage_file = f"{uuid.uuid4().hex}.db"
        stream_dump = io.BytesIO(uuid.uuid4().bytes)

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator'), \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGenerator:
            
            gen_instance = MockGenerator.return_value
            gen_instance.get_raw_stream_dump.return_value = stream_dump

            reporter = StressReporter(storage_file)
            result = reporter.get_stream_data()

            gen_instance.get_raw_stream_dump.assert_called_once()
            self.assertEqual(result, stream_dump)


class TestPortfolioStressReporter(unittest.TestCase):

    def test_run_stress_report(self):
        storage_file = f"{uuid.uuid4().hex}.db"
        symbol = f"TICKER_{uuid.uuid4().hex[:5]}"
        shifts = [random.uniform(-1.0, 1.0)]
        expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator'), \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator'):

            reporter = PortfolioStressReporter(storage_file)
            with patch.object(reporter, 'run_stress_reporting', return_value=expected_dict) as mock_reporting:
                res = reporter.run_stress_report(symbol, shifts)
                mock_reporting.assert_called_once_with(symbol, shifts)
                self.assertEqual(res, expected_dict)


class TestHelperFunctions(unittest.TestCase):

    def test_generate_stress_report(self):
        storage_file = f"{uuid.uuid4().hex}.db"
        symbol = f"SYM_{random.randint(100, 999)}"
        percentage = random.uniform(-0.5, 0.5)
        mock_output = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch('skills.market_portfolio_stress_reporter.StressReporter') as MockReporterClass:
            instance = MockReporterClass.return_value
            instance.run_stress_reporting.return_value = mock_output

            res = generate_stress_report(storage_file, symbol, percentage)

            MockReporterClass.assert_called_once_with(storage_file)
            instance.run_stress_reporting.assert_called_once_with(symbol, [percentage])
            self.assertEqual(res, mock_output)

    def test_run_stress_reporting_pipeline(self):
        storage_file = f"{uuid.uuid4().hex}.db"
        symbol = f"VAL_{uuid.uuid4().hex[:4]}"
        shifts = [random.random(), random.random()]
        pipeline_output = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioStressReporter') as MockPipelineClass:
            instance = MockPipelineClass.return_value
            instance.run_stress_report.return_value = pipeline_output

            res = run_stress_reporting_pipeline(storage_file, symbol, shifts)

            MockPipelineClass.assert_called_once_with(storage_file)
            instance.run_stress_report.assert_called_once_with(symbol, shifts)
            self.assertEqual(res, pipeline_output)


if __name__ == '__main__':
    unittest.main()