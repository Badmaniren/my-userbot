import unittest
import os
import sqlite3
import hashlib
import json
import uuid
import random
import tempfile
from unittest.mock import patch, MagicMock
import io
import requests

from skills.market_portfolio_audit_forensic_logger import (
    ForensicChainIntegrityError,
    DatabaseStorage,
    ForensicLogger,
    ForensicLogAuditor
)

class TestMarketPortfolioAuditForensicLogger(unittest.TestCase):

    def setUp(self):
        self.db_path = f":memory:"
        self.secret_salt = uuid.uuid4().hex
        self.logger = ForensicLogger(db_storage_path=self.db_path, secret_salt=self.secret_salt)

    def test_forensic_chain_integrity_validation_success(self):
        payload_1 = {uuid.uuid4().hex: uuid.uuid4().hex}
        payload_2 = {uuid.uuid4().hex: uuid.uuid4().hex}

        self.logger.log_forensic_event(payload_1)
        self.logger.log_forensic_event(payload_2)

        is_valid = self.logger.verify_chain_integrity()
        self.assertTrue(is_valid)

    def test_log_portfolio_discrepancy(self):
        portfolio_uuid = uuid.uuid4().hex
        discrepancy_code = uuid.uuid4().hex

        curr_hash = self.logger.log_portfolio_discrepancy(portfolio_uuid, discrepancy_code)
        self.assertIsInstance(curr_hash, str)
        self.assertEqual(len(curr_hash), 64)

        self.assertTrue(self.logger.verify_chain_integrity())

    def test_export_audit_trail(self):
        payload = {uuid.uuid4().hex: random.randint(1, 1000)}
        self.logger.log_forensic_event(payload)

        fd, temp_file_path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        try:
            bytes_written = self.logger.export_audit_trail(temp_file_path)
            self.assertGreater(bytes_written, 0)

            with open(temp_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 1)
            self.assertIn("payload", data[0])
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def test_ingest_external_audit_stream(self):
        url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        random_bytes = uuid.uuid4().bytes
        expected_hash = hashlib.sha256(random_bytes).hexdigest()

        mock_response = MagicMock()
        mock_response.raw = io.BytesIO(random_bytes)

        with patch('requests.get', return_value=mock_response) as mock_get:
            result_hash = self.logger.ingest_external_audit_stream(url)
            mock_get.assert_called_once_with(url)
            self.assertEqual(result_hash, expected_hash)


class TestMarketPortfolioAuditForensicLoggerIntegration(unittest.TestCase):

    def setUp(self):
        self.db_path = f":memory:"
        self.db_storage = DatabaseStorage(db_path=self.db_path)
        self.auditor = ForensicLogAuditor(db_storage=self.db_storage)

    def test_database_storage_and_auditor_flow(self):
        event_id = uuid.uuid4().hex
        discrepancy_code = uuid.uuid4().hex
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}

        logged_data = self.auditor.log_audit_event(event_id, discrepancy_code, payload)
        self.assertEqual(logged_data["event_id"], event_id)
        self.assertEqual(logged_data["discrepancy_code"], discrepancy_code)

        fetched_record = self.db_storage.get_forensic_record(event_id)
        self.assertIsNotNone(fetched_record)
        self.assertEqual(fetched_record["event_id"], event_id)
        self.assertEqual(fetched_record["discrepancy_code"], discrepancy_code)
        self.assertEqual(fetched_record["payload"], payload)

        integrity_result = self.auditor.verify_chain_integrity()
        self.assertTrue(integrity_result["is_valid"])
        self.assertEqual(integrity_result["checked_nodes_count"], 1)
        self.assertIn(fetched_record["integrity_hash"], integrity_result["hashes"])