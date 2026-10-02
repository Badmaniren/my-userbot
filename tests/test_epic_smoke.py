import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skills")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
import json

try:
    from market_portfolio_var_liquidity_core import MarketPortfolioVarLiquidityCore
    from market_portfolio_monitor import MarketPortfolioMonitor
    from market_portfolio_visualizer_v2 import MarketPortfolioVisualizerV2
except ImportError:
    from skills.market_portfolio_var_liquidity_core import MarketPortfolioVarLiquidityCore
    from skills.market_portfolio_monitor import MarketPortfolioMonitor
    from skills.market_portfolio_visualizer_v2 import MarketPortfolioVisualizerV2


class TestAdvancedOperationalControlLiquidVaR(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_data_path = "operational_var_liquidity_test_data.json"

        # Создаем реальный файл с 20-30 строками реалистичных данных ликвидного VaR для оперативного мониторинга
        realistic_records = []
        for i in range(1, 26):
            record = {
                "timestamp": f"2023-10-27T10:{i:02d}:00Z",
                "portfolio_id": "MAIN_LIQUID_BOOK_01",
                "asset_class": "EQUITY_FX",
                "var_95": round(120000.50 + i * 154.2, 2),
                "var_99": round(185000.75 + i * 210.5, 2),
                "liquidity_adjusted_var": round(210000.00 + i * 320.1, 2),
                "market_depth_score": round(0.85 - i * 0.005, 4),
                "operational_status": "NORMAL" if i < 20 else "ELEVATED_RISK"
            }
            realistic_records.append(record)

        with open(cls.test_data_path, "w", encoding="utf-8") as f:
            json.dump(realistic_records, f, indent=2)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_data_path):
            os.remove(cls.test_data_path)

    def test_liquid_var_operational_control_pipeline(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА ===")
        print(f"Загружаем реальный файл данных: {self.test_data_path}")

        with open(self.test_data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        self.assertGreaterEqual(len(raw_data), 20, "Файл должен содержать не менее 20 записей оперативного контроля")
        print(f"Успешно загружено записей: {len(raw_data)}")

        # Инициализируем модули ядра ликвидности и оперативного контроля
        core = MarketPortfolioVarLiquidityCore()
        monitor = MarketPortfolioMonitor()
        visualizer = MarketPortfolioVisualizerV2()

        # Прогоняем данные через ядро ликвидного VaR
        processed_metrics = core.evaluate_batch(raw_data)
        print(f"Ядро ликвидного VaR обработало пакетов: {len(processed_metrics)}")

        # Проверяем мониторинг на предмет выявления повышенных рисков
        alerts = monitor.check_operational_limits(processed_metrics)
        print(f"Система мониторинга сгенерировала оперативных алертов: {len(alerts)}")
        for idx, alert in enumerate(alerts):
            print(f"  [Alert {idx+1}]: {alert}")

        # Строим дашборд / визуализацию оперативного контроля
        dashboard_view = visualizer.render_dashboard(processed_metrics, alerts)
        print("Рендеринг дашборда оперативного контроля ликвидного VaR выполнен успешно.")
        print("Снимок дашборда (первые 200 символов):")
        print(f"  {str(dashboard_view)[:200]}...")

        # Утверждения для гарантии работоспособности
        self.assertIsNotNone(processed_metrics)
        self.assertIsInstance(alerts, list)
        self.assertIsNotNone(dashboard_view)
        print("=== ПРАКТИЧЕСКАЯ ПРОВЕРКА ЭПИКА УСПЕШНО ЗАВЕРШЕНА ===")

if __name__ == "__main__":
    unittest.main()
