import unittest
import uuid
import random
import hashlib
from skills.db_storage import save_audit_log_batch, get_audit_logs_by_portfolio
from skills.market_portfolio_audit_chain_validator import AuditChainValidator, validate_audit_chain


class TestMarketPortfolioAuditChainValidatorIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"portfolio_{uuid.uuid4().hex[:8]}"
        self.validator = AuditChainValidator()

    def test_audit_chain_validation_integration_flow(self):
        payload_1 = f"action_init_{random.randint(1000, 9999)}"
        record_id_1 = f"rec_{uuid.uuid4().hex[:6]}"
        prev_hash_1 = "0" * 64

        raw_str_1 = f"{prev_hash_1}:{record_id_1}:{payload_1}"
        hash_1 = hashlib.sha256(raw_str_1.encode('utf-8')).hexdigest()

        log_1 = {
            "id": record_id_1,
            "payload": payload_1,
            "prev_hash": prev_hash_1,
            "hash": hash_1,
            "sequence": 1
        }

        payload_2 = f"action_trade_{random.randint(1000, 9999)}"
        record_id_2 = f"rec_{uuid.uuid4().hex[:6]}"
        prev_hash_2 = hash_1

        raw_str_2 = f"{prev_hash_2}:{record_id_2}:{payload_2}"
        hash_2 = hashlib.sha256(raw_str_2.encode('utf-8')).hexdigest()

        log_2 = {
            "id": record_id_2,
            "payload": payload_2,
            "prev_hash": prev_hash_2,
            "hash": hash_2,
            "sequence": 2
        }

        batch = [log_1, log_2]
        save_audit_log_batch(self.portfolio_id, batch)

        is_chain_valid = self.validator.validate_chain(self.portfolio_id)
        self.assertTrue(is_chain_valid)

        func_result = validate_audit_chain(self.portfolio_id)
        self.assertIsInstance(func_result, dict)
        self.assertIn("is_valid", func_result)
        self.assertTrue(func_result["is_valid"])

    def test_audit_chain_corruption_detection(self):
        payload_1 = f"init_{random.randint(1, 100)}"
        record_id_1 = f"rec_{uuid.uuid4().hex[:6]}"
        prev_hash_1 = "0" * 64
        hash_1 = hashlib.sha256(f"{prev_hash_1}:{record_id_1}:{payload_1}".encode('utf-8')).hexdigest()

        log_1 = {
            "id": record_id_1,
            "payload": payload_1,
            "prev_hash": prev_hash_1,
            "hash": hash_1,
            "sequence": 1
        }

        log_2 = {
            "id": f"rec_{uuid.uuid4().hex[:6]}",
            "payload": "corrupted_payload",
            "prev_hash": "f" * 64,
            "hash": "e" * 64,
            "sequence": 2
        }

        save_audit_log_batch(self.portfolio_id, [log_1, log_2])

        with self.assertRaises(ValueError):
            self.validator.validate_chain(self.portfolio_id)

        func_result = validate_audit_chain(self.portfolio_id)
        self.assertFalse(func_result["is_valid"])
        self.assertEqual(func_result["broken_index"], 1)


if __name__ == "__main__":
    unittest.main()