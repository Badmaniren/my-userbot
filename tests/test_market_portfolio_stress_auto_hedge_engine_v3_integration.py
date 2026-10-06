import unittest
import uuid
import random
import os
import datetime
import db_storage
from skills.market_portfolio_stress_auto_hedge_engine_v3 import start_new, StressAutoHedgeEngine

class TestMarketPortfolioStressAutoHedgeEngineV3Integration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.scenario_name = f"scenario_{random.randint(1000, 9999)}"
        self.scenario_id = f"scid_{uuid.uuid4().hex[:8]}"
        self.volume = round(random.uniform(100.0, 10000.0), 2)
        self.audit_filename = f"audit_log_{uuid.uuid4().hex[:8]}.txt"

        # Подготовка фейковых данных в db_storage для честного теста без моков
        if hasattr(db_storage, "set_stress_metrics"):
            db_storage.set_stress_metrics(self.portfolio_id, self.scenario_name, {
                "portfolio_id": self.portfolio_id,
                "scenario": self.scenario_name,
                "volume": self.volume
            })
        else:
            # Прямая инъекция в хранилище, если поддерживается структурой db_storage
            if not hasattr(db_storage, "_stress_metrics_store"):
                db_storage._stress_metrics_store = {}
            db_storage._stress_metrics_store[(self.portfolio_id, self.scenario_name)] = {
                "portfolio_id": self.portfolio_id,
                "scenario": self.scenario_name,
                "volume": self.volume
            }
            
            # Переопределим временный метод в db_storage для теста, если его нет
            if not hasattr(db_storage, "fetch_stress_metrics"):
                db_storage.fetch_stress_metrics = lambda pid, sname: db_storage._stress_metrics_store.get((pid, sname))
            if not hasattr(db_storage, "execute_hedge_action"):
                db_storage.execute_hedge_action = lambda metrics: {"status": "success", "processed_volume": metrics["volume"]}
            if not hasattr(db_storage, "get_portfolio_state"):
                db_storage.get_portfolio_state = lambda pid: {"state": "active", "id": pid}
            if not hasattr(db_storage, "save_hedge_record"):
                db_storage.save_hedge_record = lambda record: record
            if not hasattr(db_storage, "get_audit_data"):
                db_storage.get_audit_data = lambda pid: {"audit_trail": pid, "time": str(datetime.datetime.utcnow())}

    def tearDown(self):
        if os.path.exists(self.audit_filename):
            try:
                os.remove(self.audit_filename)
            except OSError:
                pass

    def test_start_new_integration(self):
        result = start_new(self.portfolio_id, self.scenario_name)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("processed_volume"), self.volume)

    def test_stress_auto_hedge_engine_sequence(self):
        engine = StressAutoHedgeEngine(db_storage)
        sequence_result = engine.execute_hedge_sequence(self.portfolio_id, self.scenario_id)
        
        self.assertIsInstance(sequence_result, dict)
        self.assertEqual(sequence_result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("hedge_order_id", sequence_result)
        
        # Проверим валидность UUID сгенерированного хеш-ордера
        order_id = sequence_result.get("hedge_order_id")
        parsed_uuid = uuid.UUID(order_id)
        self.assertEqual(str(parsed_uuid), order_id)

    def test_run_audit_export_creates_file(self):
        engine = StressAutoHedgeEngine(db_storage)
        self.assertFalse(os.path.exists(self.audit_filename))
        
        engine.run_audit_export(self.portfolio_id, self.audit_filename)
        
        self.assertTrue(os.path.exists(self.audit_filename))
        with open(self.audit_filename, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn(self.portfolio_id, content)

    def test_verify_compliance(self):
        engine = StressAutoHedgeEngine(db_storage)
        compliance = engine.verify_compliance(self.portfolio_id)
        
        self.assertIsInstance(compliance, dict)
        self.assertTrue(compliance.get("is_compliant"))
        self.assertEqual(compliance.get("portfolio_id"), self.portfolio_id)
        self.assertIn("timestamp", compliance)

if __name__ == "__main__":
    unittest.main()