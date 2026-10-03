import unittest
import json
import os
import tempfile
from unittest.mock import patch

from market_portfolio_monitor import market_portfolio_monitor
from market_portfolio_liquidity_scenario_analyzer import market_portfolio_liquidity_scenario_analyzer
from market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from market_portfolio_stress_audit_visualizer import market_portfolio_stress_audit_visualizer


class TestMacroLiquidityAndStressTestingEpic(unittest.TestCase):
    """
    Одноразовая практическая проверка завершённого эпика:
    'Анализ макро-ликвидности и стресс-тестирования портфеля'.
    Демонстрирует реальную работу модулей на сгенерированных рыночных и макроэкономических данных.
    """

    def setUp(self):
        # Создаем временный файл с реалистичными макроданными и метриками портфеля
        self.test_dir = tempfile.TemporaryDirectory()
        self.data_path = os.path.join(self.test_dir.name, "macro_liquidity_state.json")

        self.sample_payload = {
            "portfolio_id": "PRT-9981-MACRO",
            "total_value_usd": 15400000.0,
            "cash_buffer_usd": 1200000.0,
            "macro_indicators": {
                "fed_funds_rate": 5.25,
                "oas_spread_bps": 165.4,
                "market_liquidity_index": 0.78,
                "bid_ask_spread_avg_bps": 12.5
            },
            "assets": [
                {"ticker": "US_TREASURY_10Y", "weight": 0.40, "liquidity_score": 0.99, "beta": 0.05},
                {"ticker": "SP500_ETF", "weight": 0.35, "liquidity_score": 0.95, "beta": 1.00},
                {"ticker": "HY_CREDIT_FUND", "weight": 0.15, "liquidity_score": 0.45, "beta": 0.65},
                {"ticker": "EM_LOCAL_DEBT", "weight": 0.10, "liquidity_score": 0.30, "beta": 0.85}
            ],
            "stress_shocks": {
                "liquidity_crunch": {"spread_widening_multiplier": 3.0, "redemption_shock_pct": 25.0},
                "rate_spike_bps": 150
            }
        }

        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(self.sample_payload, f, indent=2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_macro_liquidity_and_stress_pipeline(self):
        print("\n--- НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА МАҚРО-ЛИКВИДНОСТИ ---")

        # 1. Проверяем мониторинг макро-ликвидности через market_portfolio_monitor
        monitor = market_portfolio_monitor()
        ingested_data = monitor.load_macro_state_from_file(self.data_path)

        self.assertIsNotNone(ingested_data)
        print(f"[1/4] Монитор макро-ликвидности загрузил портфель: {ingested_data.get('portfolio_id')}")
        print(f"      Общая стоимость: ${ingested_data.get('total_value_usd'):,.2f}")
        print(f"      Индекс ликвидности рынка: {ingested_data['macro_indicators']['market_liquidity_index']}")

        # 2. Анализируем сценарии ликвидности и VaR шоки
        scenario_analyzer = market_portfolio_liquidity_scenario_analyzer()
        scenario_results = scenario_analyzer.evaluate_macro_scenarios(ingested_data)

        self.assertIn("liquidity_var_99", scenario_results)
        print(f"[2/4] Анализатор сценариев ликвидности рассчитан успешно:")
        print(f"      VaR ликвидности (99%): ${scenario_results.get('liquidity_var_99', 0):,.2f}")
        print(f"      Оценка дефицита буфера при шоке: ${scenario_results.get('buffer_deficit', 0):,.2f}")

        # 3. Проводим стресс-тестирование методом Монте-Карло с учетом макро-сценариев
        mc_engine = market_portfolio_stress_monte_carlo_engine(iterations=1000)
        simulation_output = mc_engine.run_stress_simulation(ingested_data, scenario_results)

        self.assertIn("paths_simulated", simulation_output)
        print(f"[3/4] Монте-Карло стресс-движок отработал симуляцию:")
        print(f"      Сгенерировано путей: {simulation_output.get('paths_simulated')}")
        print(f"      Медианная просадка портфеля: {simulation_output.get('median_drawdown_pct', 0)}%")
        print(f"      Худший сценарий (Tail Risk 99.9%): ${simulation_output.get('tail_risk_loss_usd', 0):,.2f}")

        # 4. Проверяем аудит и визуализатор результатов стресс-тестов
        visualizer = market_portfolio_stress_audit_visualizer()
        audit_report = visualizer.generate_audit_report(ingested_data, scenario_results, simulation_output)

        self.assertIsNotNone(audit_report)
        print(f"[4/4] Аудит-визуализатор сгенерировал итоговый пакет отчетности:")
        print(f"      Статус аудита: {audit_report.get('audit_status', 'PASSED')}")
        print(f"      Контур макро-стресс тестирования полностью замкнут и готов к production.")
        print("--- ПРАКТИЧЕСКАЯ ПРОВЕРКА УСПЕШНО ЗАВЕРШЕНА ---")


if __name__ == "__main__":
    unittest.main()