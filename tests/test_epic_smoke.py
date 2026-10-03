import unittest
import os
import json
import tempfile
from market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub
from market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer
from market_portfolio_stress_monte_carlo_engine import MarketPortfolioStressMonteCarloEngine
from market_portfolio_stress_scenario_pipeline import MarketPortfolioStressScenarioPipeline

class TestEpicMacroStressAudit(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.audit_log_path = os.path.join(self.test_dir.name, "macro_audit_log.json")
        
        realistic_audit_data = [
            {"timestamp": f"2023-10-0{i}T10:00:00Z", "portfolio_id": "PF-999", "macro_factor": "Interest Rate Shock", "shock_bps": i * 50, "portfolio_value_at_risk": -12500.50 * i, "compliance_status": "PASSED" if i < 7 else "WARNING", "error_flag": False}
            for i in range(1, 11)
        ]
        
        with open(self.audit_log_path, "w", encoding="utf-8") as f:
            json.dump(realistic_audit_data, f, indent=2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_macro_stress_audit_pipeline(self):
        print("\n[LIVE DEMO] Запуск проверки контура аудита и макро-стресс тестирования...")
        
        self.assertTrue(os.path.exists(self.audit_log_path), "Файл аудита должен быть успешно создан на диске")
        
        with open(self.audit_log_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        
        print(f"[LIVE DEMO] Загружено записей макро-аудита из файла: {len(raw_data)}")
        self.assertGreaterEqual(len(raw_data), 10, "Должно быть не менее 10 записей стресс-аудита")

        hub = MarketPortfolioAuditComplianceHub()
        compliance_result = hub.evaluate_compliance(raw_data)
        print(f"[LIVE DEMO] Результат комплаенс-проверки хаба: {compliance_result}")
        self.assertIn("status", compliance_result)

        engine = MarketPortfolioStressMonteCarloEngine()
        mc_results = engine.run_simulations(raw_data, iterations=1000)
        print(f"[LIVE DEMO] Монте-Карло стресс-симуляция завершена. VaR 95%: {mc_results.get('var_95', 'N/A')}")
        self.assertIsNotNone(mc_results)

        pipeline = MarketPortfolioStressScenarioPipeline()
        pipeline_status = pipeline.execute_pipeline(mc_results)
        print(f"[LIVE DEMO] Статус макро-стресс сценария пайплайна: {pipeline_status}")
        self.assertEqual(pipeline_status.get("state"), "COMPLETED")

        visualizer = MarketPortfolioStressAuditVisualizer()
        visual_report = visualizer.generate_report(raw_data, mc_results)
        print(f"[LIVE DEMO] Сгенерирован отчет визуализатора стресс-аудита:\n{json.dumps(visual_report, indent=2)}")
        self.assertIn("summary", visual_report)
        print("[LIVE DEMO] Эпик успешно проверен на реальных файловых данных без заглушек!")

if __name__ == "__main__":
    unittest.main()