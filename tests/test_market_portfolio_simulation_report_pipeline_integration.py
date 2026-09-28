import os
import unittest
import uuid
import random
from skills.market_portfolio_simulation_report_pipeline import generate_portfolio_simulation_report

class TestMarketPortfolioSimulationReportPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4()}.db"
        self.symbol = f"TICKER_{random.randint(1000, 9999)}"
        self.percentage = round(random.uniform(1.0, 15.0), 2)
        self.volume = random.randint(100, 5000)
        self.price = round(random.uniform(10.0, 500.0), 2)
        self.order_type = random.choice(["BUY", "SELL"])
        self.shifts = [round(random.uniform(-0.1, 0.1), 3) for _ in range(3)]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_simulation_report_pipeline_integration(self):
        market_context = {
            "trend": random.choice(["bullish", "bearish", "neutral"]),
            "volatility": round(random.uniform(0.01, 0.05), 4)
        }

        order_data = {
            "symbol": self.symbol,
            "volume": self.volume,
            "price": self.price,
            "order_type": self.order_type
        }

        report = generate_portfolio_simulation_report(
            storage_file=self.storage_file,
            order_data=order_data,
            market_context=market_context,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertIsInstance(report, dict)
        self.assertIn("scenario_simulation", report)
        self.assertIn("execution_pipeline", report)

        exec_data = report["execution_pipeline"]
        self.assertIsInstance(exec_data, dict)

        scenario_data = report["scenario_simulation"]
        self.assertIsInstance(scenario_data, dict)

if __name__ == "__main__":
    unittest.main()