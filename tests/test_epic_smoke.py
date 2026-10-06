import unittest
import os
import json
import tempfile
from skills.market_portfolio_stress_scenario_matrix_evaluator import market_portfolio_stress_scenario_matrix_evaluator
from skills.market_portfolio_stress_audit_visualizer import market_portfolio_stress_audit_visualizer
from skills.db_storage import db_storage

class TestPortfolioStressTestingEpicPractical(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.audit_log_path = os.path.join(self.test_dir.name, "stress_audit_report.json")

        self.mock_stress_data = [
            {"scenario_id": "SCENARIO_ALPHA", "shock_factor_pct": -15.5, "portfolio_var_usd": 125000.00, "liquidity_score": 0.82, "status": "PASSED"},
            {"scenario_id": "SCENARIO_BETA", "shock_factor_pct": -30.0, "portfolio_var_usd": 310000.50, "liquidity_score": 0.51, "status": "WARNING"},
            {"scenario_id": "SCENARIO_GAMMA", "shock_factor_pct": -50.0, "portfolio_var_usd": 750000.00, "liquidity_score": 0.22, "status": "CRITICAL"},
            {"scenario_id": "SCENARIO_DELTA", "shock_factor_pct": 10.0, "portfolio_var_usd": -45000.00, "liquidity_score": 0.95, "status": "PASSED"}
        ]

        with open(self.audit_log_path, "w", encoding="utf-8") as f:
            json.dump(self.mock_stress_data, f, indent=2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_stress_matrix_evaluation_and_audit_aggregation_real_flow(self):
        print("\n--- НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА СТРЕСС-ТЕСТИРОВАНИЯ ---")

        db = db_storage()
        evaluator = market_portfolio_stress_scenario_matrix_evaluator(db_storage_instance=db)
        visualizer = market_portfolio_stress_audit_visualizer()

        print(f"[1] Загрузка файла аудита стресс-тестов с диска: {self.audit_log_path}")
        with open(self.audit_log_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        print(f"[2] Прочитано сценариев из файла: {len(raw_data)}")
        for item in raw_data:
            print(f"    -> Сценарий: {item['scenario_id']} | Шок: {item['shock_factor_pct']}% | VaR: ${item['portfolio_var_usd']} | Статус: {item['status']}")

        print("[3] Передача матричных данных в evaluator...")
        evaluation_results = []
        for scenario in raw_data:
            eval_res = evaluator.evaluate_scenario(scenario)
            evaluation_results.append(eval_res)
            db.save(f"stress_eval_{scenario['scenario_id']}", eval_res)

        print("[4] Агрегация результатов через stress_audit_visualizer...")
        audit_summary = visualizer.generate_audit_summary(evaluation_results)

        print("\n=== ИТОГОВЫЙ АУДИТОРСКИЙ ОТЧЕТ ПО СТРЕСС-ТЕСТАМ ПОРТФЕЛЯ ===")
        print(json.dumps(audit_summary, indent=4, ensure_ascii=False))
        print("================================================================")

        self.assertIsNotNone(audit_summary, "Аудиторский отчет не должен быть пустым")
        self.assertIn("summary_metrics", audit_summary)
        print("--- ПРАКТИЧЕСКАЯ ПРОВЕРКА УСПЕШНО ЗАВЕРШЕНА ---")

if __name__ == "__main__":
    unittest.main()