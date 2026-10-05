import unittest
import json
import os
import tempfile
from unittest.mock import patch

from skills.market_portfolio_monitor import MarketPortfolioMonitor
from skills.market_portfolio_liquidity_scenario_analyzer import MarketPortfolioLiquidityScenarioAnalyzer
from skills.market_portfolio_var_liquidity_core import MarketPortfolioVarLiquidityCore
from skills.market_portfolio_stress_monte_carlo_engine import MarketPortfolioStressMonteCarloEngine

class TestMacroLiquidityAndStressTestingEpic(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file_path = os.path.join(self.temp_dir.name, "macro_liquidity_data.json")

        self.raw_market_data = [
            {"asset": "BTCUSDT", "liquidity_score": 0.85, "bid_ask_spread_bps": 2.5, "depth_usd": 15000000, "volatility": 0.04},
            {"asset": "ETHUSDT", "liquidity_score": 0.78, "bid_ask_spread_bps": 4.1, "depth_usd": 8000000, "volatility": 0.05},
            {"asset": "SOLUSDT", "liquidity_score": 0.55, "bid_ask_spread_bps": 12.0, "depth_usd": 2000000, "volatility": 0.09},
            {"asset": "ADAUSDT", "liquidity_score": 0.42, "bid_ask_spread_bps": 25.5, "depth_usd": 800000, "volatility": 0.11},
            {"asset": "XRPUSDT", "liquidity_score": 0.60, "bid_ask_spread_bps": 9.8, "depth_usd": 3500000, "volatility": 0.08}
        ]

        with open(self.data_file_path, "w", encoding="utf-8") as f:
            json.dump(self.raw_market_data, f, indent=2)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_macro_liquidity_and_stress_testing_integration(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА: СИСТЕМА МАКРО-ОЦЕНКИ ЛИКВИДНОСТИ И СТРЕСС-ТЕСТИРОВАНИЯ ===")

        self.assertTrue(os.path.exists(self.data_file_path), "Файл с рыночными данными должен существовать на диске")
        print(f"[OK] Создан реальный файл с данными на диске: {self.data_file_path}")
        print(f"[INFO] Загружено записей активов для анализа: {len(self.raw_market_data)}")

        monitor = MarketPortfolioMonitor()
        monitor_result = monitor.ingest_and_monitor(self.data_file_path)
        print(f"[MONITOR] Результат базового мониторинга макро-ликвидности портфеля: {monitor_result}")

        scenario_analyzer = MarketPortfolioLiquidityScenarioAnalyzer()
        scenario_report = scenario_analyzer.evaluate_scenarios(self.raw_market_data, shock_multiplier=2.5)
        print(f"[SCENARIO_ANALYZER] Отчет стресс-сценариев ликвидности: {json.dumps(scenario_report, indent=2)}")

        var_core = MarketPortfolioVarLiquidityCore()
        var_metrics = var_core.calculate_liquidity_var(self.raw_market_data, confidence_level=0.99)
        print(f"[VAR_CORE] Расчет VaR с поправкой на ликвидность: {json.dumps(var_metrics, indent=2)}")

        monte_carlo = MarketPortfolioStressMonteCarloEngine()
        monte_carlo_results = monte_carlo.run_simulations(self.raw_market_data, simulations_count=1000)
        print(f"[MONTE_CARLO] Стресс-тестирование (симуляций: 1000): "
              f"Max Drawdown: {monte_carlo_results.get('max_drawdown', 'N/A')}, "
              f"Probability of Default/Liquidity Crisis: {monte_carlo_results.get('liquidity_crisis_prob', 'N/A')}")

        self.assertIsNotNone(monitor_result, "Монитор ликвидности должен вернуть валидный результат")
        self.assertIn("asset_metrics", scenario_report or {}, "Анализатор сценариев должен содержать метрики по активам")
        self.assertIn("liquidity_var", var_metrics or {}, "Ядро VaR должно вернуть рассчитанные значения")
        self.assertIn("max_drawdown", monte_carlo_results or {}, "Монте-Карло должно рассчитать максимальную просадку")

        print("=== ЭПИК УСПЕШНО ПРОШЕЛ РЕАЛЬНУЮ ПРАКТИЧЕСКУЮ ПРОВЕРКУ В УСЛОВИЯХ ФАЙЛОВОГО ВВОДА/ВЫВОДА ===")

if __name__ == "__main__":
    unittest.main()
