import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_simulation_report_bridge import (
    PortfolioSimulationReportBridge,
    generate_simulation_report
)

class TestMarketPortfolioSimulationReportBridge(unittest.TestCase):

    def setUp(self):
        self.random_storage = f"{uuid.uuid4().hex}.db"
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_percentage = round(random.uniform(1.0, 50.0), 2)
        self.random_slippage = round(random.uniform(0.001, 0.05), 4)

    def test_bridge_initialization_and_composition(self):
        with patch('skills.market_portfolio_simulation_report_bridge.PortfolioScenarioSimulator') as mock_sim, \
             patch('skills.market_portfolio_simulation_report_bridge.MarketReportGenerator') as mock_rep:

            bridge = PortfolioSimulationReportBridge(self.random_storage)

            mock_sim.assert_called_once_with(self.random_storage)
            mock_rep.assert_called_once_with(self.random_storage)
            self.assertEqual(bridge.storage_file, self.random_storage)

    def test_run_simulation_and_generate_report_success(self):
        mock_sim_result = {
            "symbol": self.random_symbol,
            "percentage": self.random_percentage,
            "slippage": self.random_slippage,
            "simulated_value": random.randint(1000, 100000)
        }
        mock_report_content = f"REPORT-{uuid.uuid4().hex}"

        with patch('skills.market_portfolio_simulation_report_bridge.PortfolioScenarioSimulator') as mock_sim_cls, \
             patch('skills.market_portfolio_simulation_report_bridge.MarketReportGenerator') as mock_rep_cls:

            instance_sim = mock_sim_cls.return_value
            instance_sim.simulate_scenario.return_value = mock_sim_result

            instance_rep = mock_rep_cls.return_value
            instance_rep.generate_symbol_report.return_value = mock_report_content

            bridge = PortfolioSimulationReportBridge(self.random_storage)
            result = bridge.simulate_and_report(self.random_symbol, self.random_percentage, self.random_slippage)

            instance_sim.simulate_scenario.assert_called_once_with(
                self.random_symbol, self.random_percentage, self.random_slippage
            )
            instance_rep.generate_symbol_report.assert_called_once_with(self.random_symbol)

            self.assertIn("simulation_data", result)
            self.assertIn("report_data", result)
            self.assertEqual(result["simulation_data"], mock_sim_result)
            self.assertEqual(result["report_data"], mock_report_content)

    def test_stress_test_and_report_integration(self):
        random_shifts = [random.randint(-10, 10), random.randint(-20, 20)]
        mock_stress_result = {
            "symbol": self.random_symbol,
            "shifts": random_shifts,
            "stress_outcome": uuid.uuid4().hex
        }
        mock_stream_dump = io.BytesIO(uuid.uuid4().bytes)

        with patch('skills.market_portfolio_simulation_report_bridge.PortfolioScenarioSimulator') as mock_sim_cls, \
             patch('skills.market_portfolio_simulation_report_bridge.MarketReportGenerator') as mock_rep_cls:

            instance_sim = mock_sim_cls.return_value
            instance_sim.run_stress_test.return_value = mock_stress_result

            instance_rep = mock_rep_cls.return_value
            instance_rep.get_raw_stream_dump.return_value = mock_stream_dump

            bridge = PortfolioSimulationReportBridge(self.random_storage)
            stress_report = bridge.execute_stress_test_workflow(self.random_symbol, random_shifts)

            instance_sim.run_stress_test.assert_called_once_with(self.random_symbol, random_shifts)
            instance_rep.get_raw_stream_dump.assert_called_once()

            self.assertEqual(stress_report["stress_data"], mock_stress_result)
            self.assertEqual(stress_report["stream_dump"], mock_stream_dump)

    def test_functional_helper_generate_simulation_report(self):
        mock_sim_res = uuid.uuid4().hex
        mock_rep_res = uuid.uuid4().hex

        with patch('skills.market_portfolio_simulation_report_bridge.simulate_market_scenario') as mock_func_sim, \
             patch('skills.market_portfolio_simulation_report_bridge.generate_market_report') as mock_func_rep:

            mock_func_sim.return_value = mock_sim_res
            mock_func_rep.return_value = mock_rep_res

            res = generate_simulation_report(self.random_storage, self.random_symbol, self.random_percentage)

            mock_func_sim.assert_called_once_with(self.random_storage, self.random_symbol, self.random_percentage)
            mock_func_rep.assert_called_once_with(self.random_storage, self.random_symbol)

            self.assertEqual(res["simulation"], mock_sim_res)
            self.assertEqual(res["report"], mock_rep_res)