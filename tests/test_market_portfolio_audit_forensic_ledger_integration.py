import unittest
import uuid
import random
import json
import hashlib
from skills.market_portfolio_audit_forensic_ledger import (
    ForensicLedgerEngine,
    AuditLogIntegrityChecker,
    MarketPortfolioForensicLedger,
    IntegrityViolationException,
    ForensicLedgerException
)

class InMemoryStorageStub:
    def __init__(self):
        self.records = []

    def initialize(self):
        pass

    def save_record(self, record):
        self.records.append(record)

    def fetch_all_records(self):
        return self.records

class TestMarketPortfolioAuditForensicLedgerIntegration(unittest.TestCase):

    def setUp(self):
        self.storage = InMemoryStorageStub()
        self.ledger_engine = ForensicLedgerEngine(storage=self.storage)
        self.integrity_checker = AuditLogIntegrityChecker(ledger=self.ledger_engine)
        self.market_ledger = MarketPortfolioForensicLedger(db_storage=self.storage)

    def test_end_to_end_forensic_ledger_workflow(self):
        unique_tx_id = f"tx_{uuid.uuid4().hex}"
        unique_portfolio_id = f"port_{uuid.uuid4().hex}"
        unique_actor = f"user_{random.randint(1000, 9999)}"
        unique_action = "EXECUTE_TRADE"

        random_payload_data = {
            "portfolio_id": unique_portfolio_id,
            "asset": "BTC",
            "amount": round(random.uniform(0.1, 10.0), 4),
            "nonce": uuid.uuid4().int
        }

        audit_payload = {
            "transaction_id": unique_tx_id,
            "portfolio_id": unique_portfolio_id,
            "actor": unique_actor,
            "action": unique_action,
            "data": random_payload_data
        }

        recorded_transaction = self.ledger_engine.record_transaction(audit_payload)

        self.assertEqual(recorded_transaction["transaction_id"], unique_tx_id)
        self.assertEqual(recorded_transaction["portfolio_id"], unique_portfolio_id)
        self.assertIn("cryptographic_hash", recorded_transaction)
        self.assertIn("previous_hash", recorded_transaction)

        audit_trail = self.ledger_engine.get_audit_trail(portfolio_id=unique_portfolio_id)
        self.assertTrue(len(audit_trail) > 0)
        self.assertEqual(audit_trail[0]["transaction_id"], unique_tx_id)

        integrity_result = self.integrity_checker.verify_ledger_integrity(portfolio_id=unique_portfolio_id)
        self.assertTrue(integrity_result["is_valid"])
        self.assertEqual(integrity_result["total_records"], 1)

        tampered_payload = audit_payload.copy()
        tampered_payload["data"] = {
            "portfolio_id": unique_portfolio_id,
            "asset": "BTC",
            "amount": round(random.uniform(50.0, 100.0), 4),
            "nonce": uuid.uuid4().int
        }

        tamper_check = self.ledger_engine.detect_tampering(unique_tx_id, tampered_payload)
        self.assertTrue(tamper_check["tampered"])
        self.assertNotEqual(tamper_check["expected_hash"], tamper_check["provided_hash"])

        non_tampered_check = self.ledger_engine.detect_tampering(unique_tx_id, audit_payload)
        self.assertFalse(non_tampered_check["tampered"])
        self.assertEqual(non_tampered_check["expected_hash"], non_tampered_check["provided_hash"])

        legacy_tx_id = f"legacy_{uuid.uuid4().hex}"
        legacy_payload_str = json.dumps(random_payload_data)
        saved_tx_id = self.market_ledger.append_audit_record(
            tx_id=legacy_tx_id,
            actor=unique_actor,
            action=unique_action,
            payload=legacy_payload_str
        )
        self.assertEqual(saved_tx_id, legacy_tx_id)

        chain_valid = self.market_ledger.verify_chain_integrity()
        self.assertTrue(chain_valid)

if __name__ == "__main__":
    unittest.main()