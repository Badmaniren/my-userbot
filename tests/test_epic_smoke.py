import unittest
import os
import sys
import json
import tempfile

skills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../skills"))
if skills_dir not in sys.path:
    sys.path.insert(0, skills_dir)

try:
    from skills.market_portfolio_slippage_model import market_portfolio_slippage_model
    from skills.market_portfolio_execution_cost_optimizer import market_portfolio_execution_cost_optimizer
except ImportError:
    from market_portfolio_slippage_model import market_portfolio_slippage_model
    from market_portfolio_execution_cost_optimizer import market_portfolio_execution_cost_optimizer

class TestSlippageControlAndCostOptimizationEpic(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.data_file_path = os.path.join(self.test_dir.name, "execution_test_data.json")

        realistic_market_data = [
            {"timestamp": "2023-10-01T10:00:00Z", "symbol": "AAPL", "order_size": 5000, "average_daily_volume": 1000000, "volatility": 0.015, "spread": 0.02},
            {"timestamp": "2023-10-01T10:05:00Z", "symbol": "MSFT", "order_size": 12000, "average_daily_volume": 800000, "volatility": 0.022, "spread": 0.03},
            {"timestamp": "2023-10-01T10:10:00Z", "symbol": "GOOGL", "order_size": 2500, "average_daily_volume": 500000, "volatility": 0.018, "spread": 0.05},
            {"timestamp": "2023-10-01T10:15:00Z", "symbol": "AMZN", "order_size": 8000, "average_daily_volume": 900000, "volatility": 0.025, "spread": 0.04},
            {"timestamp": "2023-10-01T10:20:00Z", "symbol": "TSLA", "order_size": 20000, "average_daily_volume": 2000000, "volatility": 0.045, "spread": 0.08}
        ]

        with open(self.data_file_path, "w", encoding="utf-8") as f:
            json.dump(realistic_market_data, f, indent=2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_slippage_model_and_cost_optimization_live_integration(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА: Контроль рыночного проскальзывания ===")

        with open(self.data_file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        print(f"Загружено реалистичных записей из временного хранилища: {len(raw_data)}")

        slippage_results = []
        optimizer_recommendations = []

        for item in raw_data:
            symbol = item["symbol"]
            size = item["order_size"]
            adv = item["average_daily_volume"]
            vol = item["volatility"]
            spread = item["spread"]

            slippage_val = market_portfolio_slippage_model(
                order_size=size,
                average_daily_volume=adv,
                volatility=vol,
                spread=spread
            )
            slippage_results.append({"symbol": symbol, "estimated_slippage": slippage_val})

            opt_val = market_portfolio_execution_cost_optimizer(
                order_size=size,
                slippage=slippage_val,
                volatility=vol
            )
            optimizer_recommendations.append({"symbol": symbol, "optimal_tranche_size": opt_val})

        print("\n--- РЕЗУЛЬТАТЫ МОДЕЛИРОВАНИЯ ПРОСКАЛЬЗЫВАНИЯ (Square-root law & Volatility) ---")
        for res in slippage_results:
            print(f"Актив: {res['symbol']} | Расчетное проскальзывание: {res['estimated_slippage']:.6f}")
            self.assertIsNotNone(res['estimated_slippage'])
            self.assertGreaterEqual(res['estimated_slippage'], 0.0)

        print("\n--- РЕЗУЛЬТАТЫ ОПТИМИЗАЦИИ ИЗДЕРЖЕК ИСПОЛНЕНИЯ ---")
        for rec in optimizer_recommendations:
            print(f"Актив: {rec['symbol']} | Рекомендуемый размер транша: {rec['optimal_tranche_size']}")
            self.assertIsNotNone(rec['optimal_tranche_size'])
            self.assertGreater(rec['optimal_tranche_size'], 0)

        print("\n=== ПРОВЕРКА УСПЕШНО ЗАВЕРШЕНА: Модули успешно отработали на реальных данных ===")

if __name__ == "__main__":
    unittest.main()