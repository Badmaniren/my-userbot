import unittest
import uuid
import random
import os
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core
from skills.db_storage import db_storage
from skills.market_parser import market_parser

class TestMarketPortfolioVarLiquidityCoreIntegration(unittest.TestCase):

    def setUp(self):
        self.test_portfolio_id = str(uuid.uuid4())
        self.test_asset_ticker = f"TEST_{random.randint(1000, 9999)}"
        self.test_volume = round(random.uniform(1000.0, 500000.0), 2)
        self.test_confidence = random.choice([0.95, 0.99])
        self.output_file = f"var_liquidity_report_{self.test_portfolio_id}.json"

    def tearDown(self):
        if os.path.exists(self.output_file):
            try:
                os.remove(self.output_file)
            except OSError:
                pass

    def test_var_liquidity_core_end_to_end_integration(self):
        market_parser_instance = market_parser()
        raw_market_data = market_parser_instance.fetch_latest_quote(self.test_asset_ticker)

        db_storage_instance = db_storage()
        db_storage_instance.save_portfolio_position(
            portfolio_id=self.test_portfolio_id,
            ticker=self.test_asset_ticker,
            volume=self.test_volume,
            market_data=raw_market_data
        )

        core_engine = market_portfolio_var_liquidity_core()
        calculation_result = core_engine.calculate_var_and_liquidity(
            portfolio_id=self.test_portfolio_id,
            confidence_level=self.test_confidence,
            export_target=self.output_file
        )

        self.assertIsInstance(calculation_result, dict, "Результат расчета должен быть словарем")
        self.assertIn("portfolio_id", calculation_result, "Результат должен содержать portfolio_id")
        self.assertEqual(
            calculation_result["portfolio_id"], 
            self.test_portfolio_id, 
            "Идентификатор портфеля в результате должен совпадать с входным"
        )
        self.assertIn("var_value", calculation_result, "Расчет должен содержать значение VaR")
        self.assertIn("liquidity_score", calculation_result, "Расчет должен содержать оценку ликвидности")
        self.assertGreater(calculation_result["var_value"], 0.0, "VaR должен быть больше нуля")

        self.assertTrue(
            os.path.exists(self.output_file), 
            f"Интеграционный модуль должен был сгенерировать файл отчета: {self.output_file}"
        )
        
        with open(self.output_file, "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertIn(self.test_portfolio_id, file_content, "Сгенерированный файл должен содержать UUID портфеля")

if __name__ == "__main__":
    unittest.main()