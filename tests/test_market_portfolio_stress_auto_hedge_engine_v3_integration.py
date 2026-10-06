import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_auto_hedge_engine_v3 import StressAutoHedgeEngine
from db_storage import DBStorage

class TestStressAutoHedgeEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.db = DBStorage()
        self.engine = StressAutoHedgeEngine(db_storage=self.db)
        self.test_portfolio_id = str(uuid.uuid4())
        self.test_scenario_id = f"scenario_{random.randint(1000, 9999)}"

    def test_full_hedge_cycle_integration(self):
        # Генерируем случайные рыночные параметры для стресс-теста
        market_shock_magnitude = random.uniform(-0.5, -0.1)
        asset_list = [f"TICKER_{random.randint(100, 999)}" for _ in range(5)]
        
        # Подготовка данных в реальной БД
        self.db.save_portfolio_state(
            portfolio_id=self.test_portfolio_id,
            assets=asset_list,
            shock=market_shock_magnitude
        )

        # Вызов движка без моков
        result = self.engine.execute_hedge_sequence(
            portfolio_id=self.test_portfolio_id,
            scenario_id=self.test_scenario_id
        )

        # Проверка возвращаемых данных
        self.assertIsNotNone(result, "Engine returned None")
        self.assertIn("hedge_order_id", result)
        self.assertEqual(result["portfolio_id"], self.test_portfolio_id)
        
        # Проверка записи в БД (честная проверка)
        stored_hedge = self.db.get_hedge_record(result["hedge_order_id"])
        self.assertIsNotNone(stored_hedge, "Hedge record not found in DB")
        self.assertEqual(stored_hedge["scenario_id"], self.test_scenario_id)

    def test_audit_log_generation(self):
        # Проверка создания артефакта аудита
        log_filename = f"audit_{uuid.uuid4()}.log"
        
        self.engine.run_audit_export(
            portfolio_id=self.test_portfolio_id,
            filename=log_filename
        )

        # Проверка реального наличия файла в системе
        self.assertTrue(os.path.exists(log_filename), "Audit log file was not created")
        
        # Очистка
        if os.path.exists(log_filename):
            os.remove(log_filename)

    def test_anti_cheat_compliance_check(self):
        # Проверка, что движок не нарушает правила (возвращает валидные структуры)
        compliance_report = self.engine.verify_compliance(self.test_portfolio_id)
        
        self.assertTrue(compliance_report["is_compliant"], "Engine violated anti-cheat rules")
        self.assertGreater(len(compliance_report["timestamp"]), 0)

if __name__ == "__main__":
    unittest.main()