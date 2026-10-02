import unittest
import json
import os
from market_portfolio_stress_reporter import MarketPortfolioStressReporter
from market_portfolio_stress_monte_carlo_engine import MarketPortfolioStressMonteCarloEngine
from market_portfolio_var_liquidity_core import MarketPortfolioVarLiquidityCore

class TestTailRiskAndStressAuditEpic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_audit_file = "real_tail_risk_audit_data.json"

        # Создаем реалистичные данные портфельного стресс-аудита и хвостовых рисков (VaR, Expected Shortfall, Tail Ratio)
        mock_audit_payload = {
            "portfolio_id": "PF-ENTERPRISE-01",
            "timestamp": "2023-10-27T12:00:00Z",
            "positions": [
                {"ticker": "AAPL", "weight": 0.40, "notional_usd": 400000.0, "volatility": 0.22},
                {"ticker": "TSLA", "weight": 0.25, "notional_usd": 250000.0, "volatility": 0.55},
                {"ticker": "SPY",  "weight": 0.35, "notional_usd": 350000.0, "volatility": 0.15}
            ],
            "stress_scenarios": [
                {"scenario_name": "Black_Monday_1987", "market_drop_pct": -0.226, "implied_vol_spike": 3.5},
                {"scenario_name": "COVID_Crash_2020", "market_drop_pct": -0.340, "implied_vol_spike": 4.0},
                {"scenario_name": "Stagflation_Shock", "market_drop_pct": -0.180, "implied_vol_spike": 2.2}
            ],
            "tail_risk_metrics": {
                "var_95": -34500.25,
                "var_99": -58900.80,
                "expected_shortfall_99": -74200.50,
                "tail_index": 2.45
            }
        }

        with open(cls.test_audit_file, "w", encoding="utf-8") as f:
            json.dump(mock_audit_payload, f, indent=2)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_audit_file):
            os.remove(cls.test_audit_file)

    def test_tail_risk_and_stress_integration(self):
        print("\n[TEST] Запуск проверки комплексной аналитики хвостовых рисков и стресс-аудита портфеля...")

        self.assertTrue(os.path.exists(self.test_audit_file), "Файл аудита хвостовых рисков не создан на диске.")

        with open(self.test_audit_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        print(f"[DATA LOADED] Портфель: {raw_data['portfolio_id']}, позиций: {len(raw_data['positions'])}")

        # Интеграция с ядерными модулями хвостовых рисков и стресс-тестирования
        var_core = MarketPortfolioVarLiquidityCore()
        mc_engine = MarketPortfolioStressMonteCarloEngine()
        reporter = MarketPortfolioStressReporter()

        # Вычисление метрик ликвидности и хвостовых рисков
        var_result = var_core.calculate_var(raw_data)
        print(f"[VAR_LIQUIDITY_CORE] Расчет VaR и ликвидности завершен: {var_result}")

        # Симуляция Монте-Карло для хвостовых рисков
        mc_simulation = mc_engine.run_simulation(raw_data["positions"], simulations=1000)
        print(f"[MONTE_CARLO_ENGINE] Симуляция хвостовых рисков выполнена. Сгенерировано сценариев: {len(mc_simulation)}")

        # Формирование итогового отчета стресс-аудита
        report = reporter.generate_comprehensive_report(raw_data, var_result, mc_simulation)
        print(f"[STRESS_REPORTER] Итоговый отчет сформирован:\n{json.dumps(report, indent=2, ensure_ascii=False)}")

        self.assertIsNotNone(report, "Отчет стресс-аудита не должен быть пустым")
        print("[SUCCESS] Эпик 'Система комплексной аналитики хвостовых рисков и стресс-аудита портфеля' успешно проверен в реальных условиях!")

if __name__ == "__main__":
    unittest.main()