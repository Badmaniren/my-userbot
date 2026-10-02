import unittest
import json
import os
import tempfile

from market_portfolio_scenario_simulator import MarketPortfolioScenarioSimulator
from market_portfolio_stress_monte_carlo_engine import MarketPortfolioStressMonteCarloEngine
from market_portfolio_stress_reporter import MarketPortfolioStressReporter
from market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub
from market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer


class TestMarketPortfolioStressAuditVisualizerEpic(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.report_path = os.path.join(self.test_dir.name, "stress_audit_report.json")

        self.portfolio_data = {
            "portfolio_id": "PRT-9920-ALPHA",
            "total_value": 15000000.0,
            "currency": "USD",
            "assets": [
                {"ticker": "SBER", "weight": 0.40, "volatility": 0.35},
                {"ticker": "GAZP", "weight": 0.30, "volatility": 0.40},
                {"ticker": "LKOH", "weight": 0.30, "volatility": 0.30}
            ]
        }

        self.stress_params = {
            "scenario_type": "tail_risk_liquidity_crunch",
            "confidence_level": 0.99,
            "horizon_days": 10,
            "market_shock_pct": -25.5
        }

    def tearDown(self):
        self.test_dir.cleanup()

    def test_stress_scenario_audit_pipeline_real_execution(self):
        print("\n--- НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА: Визуализация и аудит стресс-сценариев портфеля ---")

        simulator = MarketPortfolioScenarioSimulator()
        simulation_result = simulator.run_scenario(self.portfolio_data, self.stress_params)
        self.assertIsNotNone(simulation_result, "Симулятор стресс-сценариев не вернул результат")
        print(f"[1] Сценарий хвостовых рисков успешно смоделирован: {json.dumps(simulation_result, ensure_ascii=False)[:120]}...")

        mc_engine = MarketPortfolioStressMonteCarloEngine(simulations=5000)
        mc_metrics = mc_engine.evaluate_tail_risk(self.portfolio_data, simulation_result)
        self.assertIn("var_99", mc_metrics)
        self.assertIn("expected_shortfall", mc_metrics)
        print(f"[2] Monte Carlo движок хвостовых рисков отработал. VaR 99%: {mc_metrics.get('var_99')}, ES: {mc_metrics.get('expected_shortfall')}")

        reporter = MarketPortfolioStressReporter(output_path=self.report_path)
        report_data = reporter.generate_report(self.portfolio_data, simulation_result, mc_metrics)
        self.assertTrue(os.path.exists(self.report_path), "Файл стресс-отчета не был создан на диске")
        print(f"[3] Генератор отчетов сформировал артефакт на диске: {self.report_path}")

        compliance_hub = MarketPortfolioAuditComplianceHub(max_allowable_drawdown_pct=20.0)
        audit_verdict = compliance_hub.audit_stress_report(report_data)
        self.assertIn("compliant", audit_verdict)
        print(f"[4] Модуль аудиторского комплаенса вынес вердикт лимитов: Комплаенс пройден = {audit_verdict.get('compliant')}, Причина: {audit_verdict.get('reason', 'N/A')}")

        visualizer = MarketPortfolioStressAuditVisualizer()
        visualization_bundle = visualizer.render_audit_dashboard(report_data, audit_verdict)
        self.assertIsNotNone(visualization_bundle)
        print(f"[5] Визуализатор стресс-аудита объединил метрики хвостовых рисков и комплаенса в дашборд: {list(visualization_bundle.keys()) if isinstance(visualization_bundle, dict) else 'Рендеринг успешен'}")

        print("--- ПРАКТИЧЕСКАЯ ПРОВЕРКА УСПЕШНО ЗАВЕРШЕНА: Все модули эпика работают на реальных данных ---")


if __name__ == "__main__":
    unittest.main()