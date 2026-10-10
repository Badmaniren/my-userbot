import unittest
import uuid
import random
import os
import tempfile

from skills.market_portfolio_predictive_var_engine import PredictiveVarEngine
from skills.market_portfolio_backtester import MarketPortfolioBacktester
from skills.market_portfolio_predictive_var_stress_validation_nexus import (
    PredictiveVarStressValidationNexus
)

class TestMarketPortfolioPredictiveVarStressValidationNexusIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, f"test_db_{uuid.uuid4().hex}.db")
        self.csv_path = os.path.join(self.temp_dir.name, f"test_data_{uuid.uuid4().hex}.csv")

        with open(self.csv_path, "w", encoding="utf-8") as f:
            f.write("date,open,high,low,close,volume\n")
            base_price = round(random.uniform(100.0, 500.0), 2)
            for i in range(30):
                p1 = base_price + random.uniform(-5.0, 5.0)
                p2 = p1 + random.uniform(-2.0, 3.0)
                f.write(f"2023-01-{i+1:02d},{base_price},{max(p1,p2)},{min(p1,p2)},{p2},{random.randint(1000,50000)}\n")
                base_price = p2

        self.portfolio_id = str(uuid.uuid4())
        self.scenario_code = f"SCENARIO_{uuid.uuid4().hex[:8]}"
        self.symbol = f"SYM_{random.randint(100, 999)}"

        self.var_engine = PredictiveVarEngine(
            db_storage=self.db_path,
            extractor_tool=None,
            market_anomaly_detector=None
        )
        self.backtester = MarketPortfolioBacktester(filepath=self.csv_path)

        self.nexus = PredictiveVarStressValidationNexus(
            var_engine=self.var_engine,
            backtester=self.backtester
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_end_to_end_validation_nexus(self):
        portfolio_value = round(random.uniform(10000.0, 1000000.0), 2)
        confidence_level = round(random.uniform(0.90, 0.99), 4)
        horizon_days = random.randint(1, 30)
        iterations = random.randint(100, 1000)
        initial_capital = round(random.uniform(5000.0, 50000.0), 2)

        scenario_params = {
            "shock_factor": round(random.uniform(0.05, 0.35), 4),
            "volatility_multiplier": round(random.uniform(1.1, 2.5), 2)
        }

        validation_result = self.nexus.run_comprehensive_validation(
            portfolio_id=self.portfolio_id,
            scenario_code=self.scenario_code,
            portfolio_value=portfolio_value,
            confidence_level=confidence_level,
            horizon_days=horizon_days,
            iterations=iterations,
            symbol=self.symbol,
            initial_capital=initial_capital,
            scenario_params=scenario_params
        )

        self.assertIsNotNone(validation_result)
        self.assertIn("predictive_var", validation_result)
        self.assertIn("backtest_summary", validation_result)
        self.assertIn("stress_validation_status", validation_result)

        summary = self.backtester.get_backtest_summary(self.symbol)
        self.assertIsNotNone(summary)

        audit_report_id = f"REPORT_{uuid.uuid4().hex[:8]}"
        loss_limit = round(portfolio_value * 0.1, 2)
        export_status = self.nexus.export_validation_audit_nexus(audit_report_id, loss_limit)
        self.assertTrue(export_status)

if __name__ == "__main__":
    unittest.main()