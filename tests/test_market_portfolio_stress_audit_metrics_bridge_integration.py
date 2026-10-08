import unittest
import uuid
import random
from skills import db_storage
from skills import market_portfolio_stress_audit_metrics_bridge as bridge


class TestMarketPortfolioStressAuditMetricsBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.db_conn = db_storage.get_connection()
        self.cursor = self.db_conn.cursor()
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS market_portfolio_stress_audit_metrics_bridge (
                session_id TEXT,
                metric_name TEXT,
                value REAL
            )
            """
        )
        self.db_conn.commit()

    def test_start_new_and_process_flow_integration(self):
        rand_session_id = str(uuid.uuid4())
        rand_metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        rand_value = round(random.uniform(10.0, 1000.0), 4)

        res_session_id = bridge.start_new(rand_session_id, rand_metric_name, rand_value)
        self.assertEqual(res_session_id, rand_session_id)

        self.cursor.execute(
            "SELECT session_id, metric_name, value FROM market_portfolio_stress_audit_metrics_bridge WHERE session_id = ?",
            (rand_session_id,)
        )
        row = self.cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], rand_session_id)
        self.assertEqual(row[1], rand_metric_name)
        self.assertEqual(row[2], rand_value)

        rand_portfolio_id = str(uuid.uuid4())
        rand_audit_id = str(uuid.uuid4())
        rand_stress_metric = round(random.uniform(-50.0, 50.0), 4)
        rand_timestamp = random.randint(1600000000, 1900000000)

        payload = {
            "portfolio_id": rand_portfolio_id,
            "audit_id": rand_audit_id,
            "stress_metric": rand_stress_metric,
            "timestamp": rand_timestamp
        }

        result = bridge.process_stress_audit_metrics_bridge(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("audit_id"), rand_audit_id)
        self.assertEqual(result.get("portfolio_id"), rand_portfolio_id)
        self.assertEqual(result.get("processed_metric"), rand_stress_metric)

        db_instance = db_storage.DatabaseStorage()
        saved_record = db_instance.get_record("stress_audit_metrics", rand_audit_id)
        self.assertIsNotNone(saved_record)
        self.assertEqual(saved_record.get("portfolio_id"), rand_portfolio_id)
        self.assertEqual(saved_record.get("audit_id"), rand_audit_id)
        self.assertEqual(saved_record.get("stress_metric"), rand_stress_metric)
        self.assertEqual(saved_record.get("timestamp"), rand_timestamp)

    def test_process_stress_audit_metrics_bridge_exceptions(self):
        with self.assertRaises(TypeError):
            bridge.process_stress_audit_metrics_bridge("not_a_dict")

        with self.assertRaises(KeyError):
            bridge.process_stress_audit_metrics_bridge({"portfolio_id": str(uuid.uuid4())})

        with self.assertRaises(ValueError):
            bridge.process_stress_audit_metrics_bridge({
                "portfolio_id": str(uuid.uuid4()),
                "audit_id": str(uuid.uuid4()),
                "stress_metric": "not_numeric"
            })


if __name__ == "__main__":
    unittest.main()
