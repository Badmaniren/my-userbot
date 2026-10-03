import unittest
import os
import json
import tempfile
from datetime import datetime

from market_portfolio_monitor import market_portfolio_monitor
from market_portfolio_liquidity_scenario_analyzer import market_portfolio_liquidity_scenario_analyzer
from market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from market_portfolio_stress_audit_visualizer import market_portfolio_stress_audit_visualizer
from db_storage import db_storage

class TestMacroLiquidityAndStressTestingEpic(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.data_file_path = os.path.join(cls.temp_dir.name, "macro_stress_input.json")
        
        realistic_market_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "portfolio_id": "PORTFOLIO_ALPHA_01",
            "total_valuation": 10000000.0,
            "assets": [
                {"ticker": "GAZP", "weight": 0.3, "liquidity_score": 0.85, "avg_daily_volume_rub": 2500000000},
                {"ticker": "SBER", "weight": 0.4, "liquidity_score": 0.95, "avg_daily_volume_rub": 5000000000},
                {"ticker": "LKOH", "weight": 0.3, "liquidity_score": 0.80, "avg_daily_volume_rub": 1800000000}
            ],
            "macro_indicators": {
                "key_rate": 16.0,
                "liquidity_deficit_rub": -1500000000000,
                "usd_rub": 92.5
            },
            "stress_scenarios": [
                {"name": "CRISIS_2008_LIKE", "market_shock_pct": -35.0, "liquidity_drain_pct": -50.0},
                {"name": "STAGFLATION_SHOCK", "market_shock_pct": -20.0, "liquidity_drain_pct": -30.0}
            ]
        }
        
        with open(cls.data_file_path, "w", encoding="utf-8") as f:
            json.dump(realistic_market_data, f, indent=2, ensure_ascii=False)
            
        cls.raw_data = realistic_market_data

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def test_01_market_portfolio_monitor_real_data(self):
        print("\n[TEST 1] Запуск market_portfolio_monitor на реальных входных данных...")
        monitor = market_portfolio_monitor()
        
        ingest_result = monitor.ingest_market_snapshot(self.data_file_path)
        self.assertTrue(ingest_result, "Монитор макро-ликвидности должен успешно прочитать файл данных.")
        
        liquidity_metrics = monitor.calculate_current_liquidity()
        print(f"  -> Рассчитанные метрики ликвидности: {liquidity_metrics}")
        
        self.assertIn("portfolio_liquidity_index", liquidity_metrics)
        self.assertGreaterEqual(liquidity_metrics["portfolio_liquidity_index"], 0.0)

    def test_02_liquidity_scenario_analyzer(self):
        print("\n[TEST 2] Проверка market_portfolio_liquidity_scenario_analyzer со сценариями макро-шоков...")
        analyzer = market_portfolio_liquidity_scenario_analyzer()
        
        analysis_report = analyzer.evaluate_scenarios(self.raw_data)
        print(f"  -> Отчет по стресс-сценариям ликвидности: {json.dumps(analysis_report, indent=2, ensure_ascii=False)}")
        
        self.assertIn("scenarios_evaluated", analysis_report)
        self.assertEqual(len(analysis_report["scenarios_evaluated"]), 2)
        self.assertTrue(any(s["scenario_name"] == "CRISIS_2008_LIKE" for s in analysis_report["scenarios_evaluated"]))

    def test_03_stress_monte_carlo_engine(self):
        print("\n[TEST 3] Запуск расчетов Монте-Карло для стресс-тестирования портфеля...")
        mc_engine = market_portfolio_stress_monte_carlo_engine(iterations=1000)
        
        mc_results = mc_engine.run_simulation(self.raw_data)
        print(f"  -> Результаты симуляции Монте-Карло VaR / Expected Shortfall: {mc_results}")
        
        self.assertIn("var_95", mc_results)
        self.assertIn("var_99", mc_results)
        self.assertIn("expected_shortfall", mc_results)
        self.assertLess(mc_results["var_95"], 0)

    def test_04_stress_audit_visualizer_and_db_persistence(self):
        print("\n[TEST 4] Генерация аудита визуализации и запись результатов в db_storage...")
        visualizer = market_portfolio_stress_audit_visualizer()
        storage = db_storage()
        
        audit_payload = {
            "epic": "Анализ макро-ликвидности и стресс-тестирования портфеля",
            "status": "COMPLETED",
            "timestamp": datetime.utcnow().isoformat(),
            "audit_visual_artifacts": visualizer.generate_audit_artifact(self.raw_data)
        }
        
        print(f"  -> Артефакты аудита и визуализации: {audit_payload['audit_visual_artifacts']}")
        
        save_status = storage.save_audit_record("macro_stress_epic", audit_payload)
        self.assertTrue(save_status, "Запись результатов эпика в БД должна завершиться успешно.")
        
        retrieved_record = storage.get_audit_record("macro_stress_epic")
        print(f"  -> Успешно прочитано из БД: {retrieved_record['status']}")
        self.assertEqual(retrieved_record["status"], "COMPLETED")

if __name__ == "__main__":
    unittest.main()