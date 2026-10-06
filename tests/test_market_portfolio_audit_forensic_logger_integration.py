import unittest
import os
import uuid
import tempfile
from skills.market_portfolio_audit_forensic_logger import (
    DatabaseStorage,
    ForensicLogger,
    ForensicLogAuditor,
    ForensicChainIntegrityError
)

class TestMarketPortfolioAuditForensicLoggerIntegration(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)

        self.export_fd, self.export_path = tempfile.mkstemp(suffix=".json")
        os.close(self.export_fd)

        self.secret_salt = str(uuid.uuid4())
        self.logger = ForensicLogger(db_storage_path=self.db_path, secret_salt=self.secret_salt)

        self.db_storage = DatabaseStorage(db_path=self.db_path)
        self.auditor = ForensicLogAuditor(db_storage=self.db_storage)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        if os.path.exists(self.export_path):
            os.remove(self.export_path)

    def test_forensic_logger_and_auditor_integration(self):
        portfolio_uuid_1 = str(uuid.uuid4())
        discrepancy_code_1 = f"DISC_{uuid.uuid4().hex[:6].upper()}"

        hash_1 = self.logger.log_portfolio_discrepancy(portfolio_uuid_1, discrepancy_code_1)
        self.assertTrue(isinstance(hash_1, str))
        self.assertEqual(len(hash_1), 64)

        event_id_2 = str(uuid.uuid4())
        discrepancy_code_2 = f"DISC_{uuid.uuid4().hex[:6].upper()}"
        payload_2 = {"metric": uuid.random.randint(100, 999), "status": "investigation_required"}

        audit_res = self.auditor.log_audit_event(
            event_id=event_id_2,
            discrepancy_code=discrepancy_code_2,
            payload=payload_2
        )

        self.assertEqual(audit_res["event_id"], event_id_2)
        self.assertEqual(audit_res["discrepancy_code"], discrepancy_code_2)
        self.assertEqual(audit_res["payload"], payload_2)

        fetched_record = self.db_storage.get_forensic_record(event_id_2)
        self.assertIsNotNone(fetched_record)
        self.assertEqual(fetched_record["event_id"], event_id_2)
        self.assertEqual(fetched_record["discrepancy_code"], discrepancy_code_2)
        self.assertEqual(fetched_record["payload"], payload_2)

        is_logger_chain_valid = self.logger.verify_chain_integrity()
        self.assertTrue(is_logger_chain_valid)

        audit_verification = self.auditor.verify_chain_integrity()
        self.assertTrue(audit_verification["is_valid"])
        self.assertEqual(audit_verification["checked_nodes_count"], 2)
        self.assertEqual(len(audit_verification["hashes"]), 2)

        exported_bytes = self.logger.export_audit_trail(self.export_path)
        self.assertGreater(exported_bytes, 0)
        self.assertTrue(os.path.exists(self.export_path))

        with open(self.export_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(portfolio_uuid_1, content)
            self.assertIn(event_id_2, content)

    def test_chain_integrity_violation_raises_error(self):
        portfolio_uuid = str(uuid.uuid4())
        code_a = f"ERR_{uuid.uuid4().hex[:4]}"
        code_b = f"ERR_{uuid.uuid4().hex[:4]}"

        self.logger.log_portfolio_discrepancy(portfolio_uuid, code_a)
        self.logger.log_portfolio_discrepancy(portfolio_uuid, code_b)

        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE forensic_audit_logs SET payload = ? WHERE id = 1", (json.dumps({"tampered": True}),))
        conn.commit()
        conn.close()

        with self.assertRaises(ForensicChainIntegrityError):
            self.logger.verify_chain_integrity()

if __name__ == '__main__':
    unittest.main()