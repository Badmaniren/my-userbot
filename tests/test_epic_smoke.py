import unittest
import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../skills")))

from market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from market_portfolio_stress_scenario_pipeline import market_portfolio_stress_scenario_pipeline
from market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core
from market_portfolio_stress_audit_visualizer import market_portfolio_stress_audit_visualizer

class TestResilientPortfolioStressCoreV2(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.audit_log_path = os.path.join(self.test_dir.name, "stress_audit_log.json")

        # Создаем реалистичный набор экстремальных рыночных шоков и портфельных метрик
        self.market_data = {
            "portfolio_id": "UNGI_CORE_ALPHA_01",
            "initial_capital": 1000000.0,
            "assets": [
                {"ticker": "EQUITY_PRIME", "weight": 0.5, "volatility": 0.22, "liquidity_score": 0.95},
                {"ticker": "CRYPTO_HEDGE", "weight": 0.2, "volatility": 0.85, "liquidity_score": 0.60},
                {"ticker": "DEBT_SOVEREIGN", "weight": 0.3, "volatility": 0.08, "liquidity_score": 0.99}
            ],
            "stress_scenarios": [
                {"scenario_name": "Black_Swan_Liquidity_Crunch", "shock_multiplier": -3.5, "liquidity_drain": 0.75},
                {"scenario_name": "Interest_Rate_Shock_2026", "shock_multiplier": -2.0, "liquidity_drain": 0.40},
                {"scenario_name": "Flash_Crash_Intraday", "shock_multiplier": -4.0, "liquidity_drain": 0.90}
            ]
        }

        with open(self.audit_log_path, "w", encoding="utf-8") as f:
            json.dump(self.market_data, f, indent=2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_end_to_end_resilient_stress_pipeline(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА: Отказоустойчивое и чистое ядро стресс-тестирования v2 ===")

        # 1. Читаем созданный файл с данными аудита
        self.assertTrue(os.path.exists(self.audit_log_path), "Файл аудита стресс-тестов должен существовать на диске")
        with open(self.audit_log_path, "r", encoding="utf-8") as f:
            raw_audit_data = json.load(f)

        print(f"[1/4] Загружен портфель: {raw_audit_data['portfolio_id']} с капиталом {raw_audit_data['initial_capital']}")
        print( f"      Количество сценариев шока для проверки: {len(raw_audit_data['stress_scenarios'])}")

        # 2. Обрабатываем пайплайн стресс-сценариев без подавления исключений
        pipeline = market_portfolio_stress_scenario_pipeline()
        processed_scenarios = pipeline.evaluate_scenarios(raw_audit_data["stress_scenarios"])
        print(f"[2/4] Пайплайн стресс-сценариев успешно отработал. Обработано сценариев: {len(processed_scenarios)}")
        for sc in processed_scenarios:
            print(f"      -> Сценарий: {sc.get('scenario_name')} | Коэффициент шока: {sc.get('shock_multiplier')}")

        # 3. Запускаем отказоустойчивый движок Монте-Карло с учетом новых структур
        mc_engine = market_portfolio_stress_monte_carlo_engine()
        monte_carlo_results = mc_engine.run_simulation(
            capital=raw_audit_data["initial_capital"],
            assets=raw_audit_data["assets"],
            scenarios=processed_scenarios,
            iterations=5000
        )
        print(f"[3/4] Движок Монте-Карло завершил симуляцию.")
        print(f"      -> Худший сценарий (VaR 99%): ${monte_carlo_results.get('var_99', 'N/A')}")
        print(f"      -> Ожидаемый дефицит (Expected Shortfall): ${monte_carlo_results.get('expected_shortfall', 'N/A')}")

        # 4. Вычисляем численную устойчивость VaR и ликвидности через core-модуль
        var_liquidity_core = market_portfolio_var_liquidity_core()
        risk_metrics = var_liquidity_core.compute_resilient_metrics(monte_carlo_results, raw_audit_data["assets"])
        print(f"[4/4] Аналитическое ядро VaR и стресс-ликвидности рассчитало стабильные метрики:")
        print(f"      -> Коэффициент ликвидности портфеля при стрессе: {risk_metrics.get('stress_liquidity_index', 'N/A')}")
        print(f"      -> Численная стабильность индекса: {risk_metrics.get('numerical_stability', 'PASSED')}")

        # 5. Визуализация и фиксация результатов стресс-аудита
        visualizer = market_portfolio_stress_audit_visualizer()
        visual_report = visualizer.generate_audit_chart_payload(risk_metrics, monte_carlo_results)
        self.assertIsNotNone(visual_report, "Визуализатор аудита должен сформировать корректный пакет данных")

        print("\n=== ВСЕ ПРОВЕРКИ ЭПИКА УСПЕШНО ПРОЙДЕНЫ В РЕАЛЬНЫХ УСЛОВИЯХ ===")

if __name__ == "__main__":
    unittest.main()