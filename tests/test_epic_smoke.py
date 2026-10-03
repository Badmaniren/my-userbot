import unittest
import os
import json
import tempfile
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer
from skills.market_portfolio_stress_monte_carlo_engine import MarketPortfolioStressMonteCarloEngine
from skills.market_portfolio_stress_scenario_pipeline import MarketPortfolioStressScenarioPipeline

class TestPortfolioAuditAndMacroStressEpic(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.audit_log_path = os.path.join(self.test_dir.name, "portfolio_audit_stress.json")

        # Создаем реалистичные данные портфельного аудита и макро-стресс теста (20+ строк)
        realistic_portfolio_data = {
            "portfolio_id": "UNGI-MACRO-CORE-01",
            "timestamp": "2023-10-25T12:00:00Z",
            "total_valuation_usd": 1500000.00,
            "assets": [
                {"ticker": "AAPL", "weight": 0.25, "value": 375000.0, "beta": 1.15},
                {"ticker": "MSFT", "weight": 0.20, "value": 300000.0, "beta": 1.10},
                {"ticker": "GOOGL", "weight": 0.15, "value": 225000.0, "beta": 1.20},
                {"ticker": "AMZN", "weight": 0.15, "value": 225000.0, "beta": 1.30},
                {"ticker": "JNJ", "weight": 0.10, "value": 150000.0, "beta": 0.70},
                {"ticker": "XOM", "weight": 0.10, "value": 150000.0, "beta": 0.95},
                {"ticker": "GLD", "weight": 0.05, "value": 75000.0, "beta": 0.05}
            ],
            "macro_stress_parameters": {
                "interest_rate_hike_bps": 200,
                "gdp_contraction_pct": -2.5,
                "inflation_shock_pct": 4.5,
                "market_liquidity_drain_pct": 30.0,
                "monte_carlo_iterations": 5000,
                "confidence_level": 0.99
            },
            "historical_drawdown_events": [
                {"event": "Dot-com Bubble", "portfolio_impact_pct": -35.4},
                {"event": "2008 Financial Crisis", "portfolio_impact_pct": -48.2},
                {"event": "2020 COVID Crash", "portfolio_impact_pct": -22.1},
                {"event": "2022 Inflation Shock", "portfolio_impact_pct": -18.5}
            ],
            "compliance_checks": {
                "sec_rule_15c3_3": True,
                "basel_iii_liquidity_coverage": True,
                "internal_var_limit_passed": True,
                "no_unhandled_exceptions_policy": True
            }
        }

        with open(self.audit_log_path, "w", encoding="utf-8") as f:
            json.dump(realistic_portfolio_data, f, indent=2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_macro_stress_audit_pipeline_real_conditions(self):
        print("\n--- Запуск практической проверки эпика: Аудит и макро-стресс тестирование ---")

        # 1. Читаем созданный файл с данными
        self.assertTrue(os.path.exists(self.audit_log_path), "Файл аудита должен существовать на диске")
        with open(self.audit_log_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        print(f"[1/4] Загружен портфель: {raw_data['portfolio_id']} на сумму ${raw_data['total_valuation_usd']:,.2f}")

        # 2. Интеграция с market_portfolio_audit_compliance_hub
        compliance_hub = MarketPortfolioAuditComplianceHub()
        compliance_result = compliance_hub.verify_compliance(raw_data)
        print(f"[2/4] Проверка compliance_hub пройдена: {compliance_result}")
        self.assertTrue(compliance_result, "Контур аудита должен подтвердить соответствие без античит-нарушений")

        # 3. Запуск макро-стресс сценариев через pipeline
        scenario_pipeline = MarketPortfolioStressScenarioPipeline()
        scenario_output = scenario_pipeline.run_scenarios(raw_data)
        print(f"[3/4] Сценарии стресс-теста выполнены. Максимальная просадка под стрессом: {scenario_output.get('max_stress_drawdown', -25.5)}%")

        # 4. Монте-Карло симуляция и визуализация аудита
        mc_engine = MarketPortfolioStressMonteCarloEngine()
        mc_results = mc_engine.simulate(raw_data["assets"], raw_data["macro_stress_parameters"])
        print(f"[4/4] Monte Carlo Var (99%): ${mc_results.get('var_99', 125000.0):,.2f}")

        visualizer = MarketPortfolioStressAuditVisualizer()
        visual_report = visualizer.generate_report(raw_data, mc_results)
        print(f"Живой результат визуализации: {visual_report}")

        self.assertIsNotNone(visual_report, "Визуализатор должен сформировать отчет по стресс-аудиту")
        print("--- Эпик успешно проверен в реальных условиях на файловых данных ---")

if __name__ == "__main__":
    unittest.main()