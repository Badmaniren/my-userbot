import unittest
import os
import uuid
import random
from skills.market_portfolio_simulation_report_bridge import run_simulation_and_generate_report, PortfolioSimulationReportBridge
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
from skills.market_report_generator import MarketReportGenerator

class TestMarketPortfolioSimulationReportBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.unique_id = str(uuid.uuid4())[:8]
        self.storage_file = f"test_storage_{self.unique_id}.json"
        self.symbol = f"TICK_{self.unique_id.upper()}"
        self.percentage = round(random.uniform(1.0, 15.0), 2)

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write('{"test": "data"}')

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

        report_file = f"{self.symbol}_report.txt"
        if os.path.exists(report_file):
            os.remove(report_file)

    def test_simulation_report_bridge_integration(self):
        bridge = PortfolioSimulationReportBridge(storage_file=self.storage_file)
        self.assertIsInstance(bridge.simulator, PortfolioScenarioSimulator)
        self.assertIsInstance(bridge.generator, MarketReportGenerator)

        result = bridge.process_simulation_and_report(symbol=self.symbol, percentage=self.percentage)

        self.assertIn("simulation_result", result)
        self.assertIn("report_data", result)
        self.assertEqual(result["symbol"], self.symbol)

        report_file_name = f"{self.symbol}_report.txt"
        if os.path.exists(report_file_name):
            os.remove(report_file_name)

    def test_functional_bridge_wrapper(self):
        report_output = run_simulation_and_generate_report(
            storage_file=self.storage_file,
            symbol=self.symbol,
            percentage=self.percentage
        )

        self.assertIsNotNone(report_output)
        self.assertIsInstance(report_output, (str, dict))

if __name__ == "__main__":
    unittest.main()