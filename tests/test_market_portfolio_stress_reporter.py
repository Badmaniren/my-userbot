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

    def test_run_stress_reporting_logic(self):
        rnd_storage = f"vault_{uuid.uuid4().hex}.db"
        rnd_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        rnd_shift = random.uniform(-0.5, 0.5)
        rnd_sim_res = {"sim_id": uuid.uuid4().hex, "loss": random.randint(100, 1000)}
        rnd_base_rep = {"report_uuid": uuid.uuid4().hex, "status": "AUDITED"}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim_cls, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as mock_gen_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.run_stress_test.return_value = rnd_sim_res

            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.generate_symbol_report.return_value = rnd_base_rep

            reporter = StressReporter(rnd_storage)
            result = reporter.run_stress_reporting(rnd_symbol, [rnd_shift])

            self.assertIn("simulation_results", result)
            self.assertIn("base_report", result)
            self.assertIn("compact_text_report", result)
            self.assertIn("tabular_report", result)
            self.assertIn("chart_export", result)

            self.assertEqual(result["simulation_results"], rnd_sim_res)
            self.assertEqual(result["base_report"], rnd_base_rep)
            self.assertIn(rnd_symbol, result["compact_text_report"])
            self.assertEqual(result["tabular_report"][0]["symbol"], rnd_symbol)
            self.assertEqual(result["tabular_report"][0]["shifts"], [rnd_shift])
            self.assertEqual(result["tabular_report"][0]["results"], rnd_sim_res)
            self.assertEqual(result["chart_export"]["type"], "line")
            self.assertEqual(result["chart_export"]["data"], rnd_sim_res)

            mock_sim_instance.run_stress_test.assert_called_once_with(rnd_symbol, [rnd_shift])
            mock_gen_instance.generate_symbol_report.assert_called_once_with(rnd_symbol)

    def test_simulate_single_success(self):
        rnd_storage = f"vault_{uuid.uuid4().hex}.db"
        rnd_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        rnd_pct = random.uniform(-1.0, 1.0)
        rnd_output = {"scenario_exec_id": uuid.uuid4().hex, "impact": random.random()}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim_cls:
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = rnd_output

            reporter = StressReporter(rnd_storage)
            res = reporter.simulate_single(rnd_symbol, rnd_pct)

            self.assertEqual(res, rnd_output)
            mock_sim_instance.simulate_scenario.assert_called_once_with(rnd_symbol, rnd_pct)

    def test_simulate_single_key_error(self):
        rnd_storage = f"vault_{uuid.uuid4().hex}.db"
        rnd_symbol = f"BAD_{uuid.uuid4().hex[:6].upper()}"
        rnd_pct = random.uniform(-1.0, 1.0)

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim_cls:
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.side_effect = KeyError("Not found")

            reporter = StressReporter(rnd_storage)
            res = reporter.simulate_single(rnd_symbol, rnd_pct)

            self.assertEqual(res, {})

    def test_get_stream_data(self):
        rnd_storage = f"vault_{uuid.uuid4().hex}.db"
        rnd_dump = [uuid.uuid4().hex, uuid.uuid4().hex, random.randint(1, 100)]

        with patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as mock_gen_cls:
            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.get_raw_stream_dump.return_value = rnd_dump

            reporter = StressReporter(rnd_storage)
            dump = reporter.get_stream_data()

            self.assertEqual(dump, rnd_dump)
            mock_gen_instance.get_raw_stream_dump.assert_called_once()


class TestPortfolioStressReporter(unittest.TestCase):

    def test_portfolio_stress_reporter_inheritance(self):
        rnd_storage = f"vault_{uuid.uuid4().hex}.db"
        rnd_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        rnd_shifts = [random.uniform(-0.2, 0.2), random.uniform(0.1, 0.5)]
        rnd_expected = {"pipeline_status": uuid.uuid4().hex}

        with patch.object(StressReporter, 'run_stress_reporting', return_value=rnd_expected) as mock_super_run:
            reporter = PortfolioStressReporter(rnd_storage)
            res = reporter.run_stress_report(rnd_symbol, rnd_shifts)

            self.assertEqual(res, rnd_expected)
            mock_super_run.assert_called_once_with(rnd_symbol, rnd_shifts)


class TestFunctionalHelpers(unittest.TestCase):

    def test_generate_stress_report_helper(self):
        rnd_storage = f"vault_{uuid.uuid4().hex}.db"
        rnd_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        rnd_pct = random.uniform(-0.5, 0.5)
        rnd_payload = {"report_key": uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.StressReporter') as mock_reporter_cls:
            mock_reporter_instance = mock_reporter_cls.return_value
            mock_reporter_instance.run_stress_reporting.return_value = rnd_payload

            res = generate_stress_report(rnd_storage, rnd_symbol, rnd_pct)

            self.assertEqual(res, rnd_payload)
            mock_reporter_cls.assert_called_once_with(rnd_storage)
            mock_reporter_instance.run_stress_reporting.assert_called_once_with(rnd_symbol, [rnd_pct])

    def test_run_stress_reporting_pipeline_helper(self):
        rnd_storage = f"vault_{uuid.uuid4().hex}.db"
        rnd_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        rnd_shifts = [random.uniform(-0.1, 0.1)]
        rnd_payload = {"pipeline_id": uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioStressReporter') as mock_reporter_cls:
            mock_reporter_instance = mock_reporter_cls.return_value
            mock_reporter_instance.run_stress_report.return_value = rnd_payload

            res = run_stress_reporting_pipeline(rnd_storage, rnd_symbol, rnd_shifts)

            self.assertEqual(res, rnd_payload)
            mock_reporter_cls.assert_called_once_with(rnd_storage)
            mock_reporter_instance.run_stress_report.assert_called_once_with(rnd_symbol, rnd_shifts)


if __name__ == '__main__':
    unittest.main()