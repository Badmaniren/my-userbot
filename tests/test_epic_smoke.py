import unittest
import os
import sys
import tempfile
import json

skills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'skills'))
if skills_dir not in sys.path:
    sys.path.insert(0, skills_dir)

try:
    from market_portfolio_var_liquidity_core import LiquidityAdjustedVaRCalculator
    from market_portfolio_valuation import PortfolioValuationEngine
except ImportError:
    from skills.market_portfolio_var_liquidity_core import LiquidityAdjustedVaRCalculator
    from skills.market_portfolio_valuation import PortfolioValuationEngine

class TestLiquidityAdjustedVaRIntegration(unittest.TestCase):

    def setUp(self):
        self.test_data = {
            "portfolio_id": "TEST_PORTFOLIO_LIQUIDITY_001",
            "assets": [
                {"ticker": "AAPL", "weight": 0.4, "volatility": 0.25, "average_daily_volume": 50000000, "position_size": 20000},
                {"ticker": "ILLQ", "weight": 0.6, "volatility": 0.45, "average_daily_volume": 150000, "position_size": 150000}
            ],
            "confidence_level": 0.95,
            "horizon_days": 1
        }

        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = os.path.join(self.temp_dir.name, "portfolio_var_test.json")
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.test_data, f, indent=2)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_liquidity_adjusted_var_calculation_pipeline(self):
        print(f"\n[INFO] Загрузка тестового портфеля из файла: {self.file_path}")
        with open(self.file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        print(f"[INFO] Данные портфеля: ID={raw_data['portfolio_id']}, Активов={len(raw_data['assets'])}")

        valuation_engine = PortfolioValuationEngine()
        base_valuation = valuation_engine.evaluate(raw_data)
        print(f"[RESULT] Базовая оценка портфеля прошла успешно. Стоимость: {base_valuation}")

        var_calculator = LiquidityAdjustedVaRCalculator()

        calculated_var = var_calculator.compute_var(
            assets=raw_data["assets"],
            confidence_level=raw_data["confidence_level"],
            horizon_days=raw_data["horizon_days"]
        )

        print("\n=== РЕЗУЛЬТАТЫ РАСЧЕТА VaR С ПОПРАВКОЙ НА ЛИКВИДНОСТЬ ===")
        print(f"Чистый (Standard) VaR: {calculated_var.get('standard_var', 'N/A')}")
        print(f"Коэффициент корректировки ликвидности (Liquidity Penalty): {calculated_var.get('liquidity_adjustment_factor', 'N/A')}")
        print(f"Итоговый VaR с поправкой на ликвидность: {calculated_var.get('liquidity_adjusted_var', 'N/A')}")
        print(f"Статус валидации метрик: {calculated_var.get('validation_status', 'PASSED')}")
        print("==========================================================")

        self.assertIn("liquidity_adjusted_var", calculated_var)
        self.assertGreater(calculated_var["liquidity_adjusted_var"], 0)
        self.assertEqual(calculated_var.get("validation_status", "PASSED"), "PASSED")

if __name__ == "__main__":
    unittest.main()