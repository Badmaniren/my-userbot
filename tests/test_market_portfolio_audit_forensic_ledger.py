import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import json

from skills.market_portfolio_audit_forensic_ledger import (
    ForensicLedgerException,
    IntegrityViolationException,
    MarketPortfolioForensicLedger,
    ForensicLedgerEngine,
    AuditLogIntegrityChecker
)

class TestMarketPortfolioAuditForensicLedger(unittest.TestCase):
    def setUp(self):
        self.salt = uuid.uuid4().hex
        self.ledger = MarketPortfolioForensicLedger(db_storage=None, secret_salt=self.salt)

    def test_init_with_storage_failure(self):
        mock_storage = MagicMock()
        mock_storage.initialize.side_effect = Exception(uuid.uuid4().hex)
        with self.assertRaises(ForensicLedgerException):
            MarketPortfolioForensicLedger(db_storage=mock_storage, secret_salt=self.salt)

    def test_append_audit_record_success(self):
        tx_id = uuid.uuid4().hex
        actor = uuid.uuid4().hex
        action = uuid.uuid4().hex
        payload = uuid.uuid4().hex

        mock_storage = MagicMock()
        ledger = MarketPortfolioForensicLedger(db_storage=mock_storage, secret_salt=self.salt)

        res = ledger.append_audit_record(tx_id, actor, action, payload)
        self.assertEqual(res, tx_id)
        mock_storage.save_record.assert_called_once()

    def test_append_audit_record_failure(self):
        tx_id = uuid.uuid4().hex
        actor = uuid.uuid4().hex
        action = uuid.uuid4().hex
        payload = uuid.uuid4().hex

        mock_storage = MagicMock()
        mock_storage.save_record.side_effect = Exception(uuid.uuid4().hex)
        ledger = MarketPortfolioForensicLedger(db_storage=mock_storage, secret_salt=self.salt)

        with self.assertRaises(ForensicLedgerException):
            ledger.append_audit_record(tx_id, actor, action, payload)

    def test_verify_chain_integrity_no_storage(self):
        ledger = MarketPortfolioForensicLedger(db_storage=None, secret_salt=self.salt)
        self.assertTrue(ledger.verify_chain_integrity())

    def test_verify_chain_integrity_empty_records(self):
        mock_storage = MagicMock()
        mock_storage.fetch_all_records.return_value = []
        ledger = MarketPortfolioForensicLedger(db_storage=mock_storage, secret_salt=self.salt)
        self.assertTrue(ledger.verify_chain_integrity())

    def test_verify_chain_integrity_success(self):
        tx_id = uuid.uuid4().hex
        payload = uuid.uuid4().hex
        prev_hash = "0" * 64
        payload_str = f"{prev_hash}:{tx_id}:{payload}"
        import hashlib
        h = hashlib.sha256(payload_str.encode()).hexdigest()

        record = {
            "tx_id": tx_id,
            "payload": payload,
            "hash": h,
            "prev_hash": prev_hash
        }

        mock_storage = MagicMock()
        mock_storage.fetch_all_records.return_value = [record]
        ledger = MarketPortfolioForensicLedger(db_storage=mock_storage, secret_salt=self.salt)

        self.assertTrue(ledger.verify_chain_integrity())

    def test_verify_chain_integrity_prev_hash_violation(self):
        tx_id = uuid.uuid4().hex
        payload = uuid.uuid4().hex
        record = {
            "tx_id": tx_id,
            "payload": payload,
            "hash": "a" * 64,
            "prev_hash": "b" * 64
        }

        mock_storage = MagicMock()
        mock_storage.fetch_all_records.return_value = [record]
        ledger = MarketPortfolioForensicLedger(db_storage=mock_storage, secret_salt=self.salt)

        with self.assertRaises(IntegrityViolationException):
            ledger.verify_chain_integrity()

    def test_verify_chain_integrity_hash_violation(self):
        tx_id = uuid.uuid4().hex
        payload = uuid.uuid4().hex
        prev_hash = "0" * 64
        record = {
            "tx_id": tx_id,
            "payload": payload,
            "hash": "f" * 64,
            "prev_hash": prev_hash
        }

        mock_storage = MagicMock()
        mock_storage.fetch_all_records.return_value = [record]
        ledger = MarketPortfolioForensicLedger(db_storage=mock_storage, secret_salt=self.salt)

        with self.assertRaises(IntegrityViolationException):
            ledger.verify_chain_integrity()

    def test_verify_chain_integrity_exception_wrapper(self):
        mock_storage = MagicMock()
        mock_storage.fetch_all_records.side_effect = Exception(uuid.uuid4().hex)
        ledger = MarketPortfolioForensicLedger(db_storage=mock_storage, secret_salt=self.salt)

        with self.assertRaises(ForensicLedgerException):
            ledger.verify_chain_integrity()

    def test_export_ledger(self):
        chunk_data = uuid.uuid4().hex.encode()
        stream = io.BytesIO(chunk_data)
        mock_storage = MagicMock()
        mock_storage.get_raw_ledger_stream.return_value = stream

        exporter = io.BytesIO()
        ledger = MarketPortfolioForensicLedger(db_storage=mock_storage, secret_salt=self.salt)
        ledger.export_ledger(exporter)

        self.assertEqual(exporter.getvalue(), chunk_data)

    def test_export_ledger_exception(self):
        mock_storage = MagicMock()
        mock_storage.get_raw_ledger_stream.side_effect = Exception(uuid.uuid4().hex)
        exporter = io.BytesIO()
        ledger = MarketPortfolioForensicLedger(db_storage=mock_storage, secret_salt=self.salt)

        with self.assertRaises(ForensicLedgerException):
            ledger.export_ledger(exporter)

    def test_forensic_ledger_engine_record_and_get(self):
        engine = ForensicLedgerEngine()
        tx_id = uuid.uuid4().hex
        portfolio_id = uuid.uuid4().hex
        payload = {
            "transaction_id": tx_id,
            "portfolio_id": portfolio_id,
            "amount": random.randint(1, 1000)
        }

        rec = engine.record_transaction(payload)
        self.assertEqual(rec["transaction_id"], tx_id)
        self.assertIn("cryptographic_hash", rec)
        self.assertIn("previous_hash", rec)

        trail = engine.get_audit_trail(portfolio_id=portfolio_id)
        self.assertEqual(len(trail), 1)
        self.assertEqual(trail[0]["transaction_id"], tx_id)

        full_trail = engine.get_audit_trail()
        self.assertEqual(len(full_trail), 1)

    def test_forensic_ledger_engine_detect_tampering(self):
        engine = ForensicLedgerEngine()
        tx_id = uuid.uuid4().hex
        payload = {
            "transaction_id": tx_id,
            "data": uuid.uuid4().hex
        }
        engine.record_transaction(payload)

        res_clean = engine.detect_tampering(tx_id, payload)
        self.assertFalse(res_clean["tampered"])

        tampered_payload = {
            "transaction_id": tx_id,
            "data": uuid.uuid4().hex
        }
        res_tampered = engine.detect_tampering(tx_id, tampered_payload)
        self.assertTrue(res_tampered["tampered"])

        res_not_found = engine.detect_tampering(uuid.uuid4().hex, payload)
        self.assertTrue(res_not_found["tampered"])

    def test_audit_log_integrity_checker(self):
        ledger = ForensicLedgerEngine()
        tx_id = uuid.uuid4().hex
        portfolio_id = uuid.uuid4().hex
        ledger.record_transaction({
            "transaction_id": tx_id,
            "portfolio_id": portfolio_id
        })

        checker = AuditLogIntegrityChecker(ledger=ledger)
        res = checker.verify_ledger_integrity(portfolio_id=portfolio_id)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["total_records"], 1)

        checker_no_ledger = AuditLogIntegrityChecker(ledger=None)
        res_empty = checker_no_ledger.verify_ledger_integrity()
        self.assertTrue(res_empty["is_valid"])
        self.assertEqual(res_empty["total_records"], 0)