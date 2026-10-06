import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import types

class TestMarketPortfolioAuditSnapshotVerifier(unittest.TestCase):

    def setUp(self):
        self.random_prefix = uuid.uuid4().hex[:8]
        self.snapshot_id = f"snap_{uuid.uuid4().hex}"
        self.portfolio_id = f"port_{uuid.uuid4().hex}"
        self.expected_hash = uuid.uuid4().hex

    def test_verify_snapshot_success(self):
        mock_db = MagicMock()
        mock_db.get_snapshot.return_value = {
            "snapshot_id": self.snapshot_id,
            "portfolio_id": self.portfolio_id,
            "integrity_hash": self.expected_hash,
            "status": "VALID"
        }

        with patch.dict(sys.modules, {'db_storage': mock_db}):
            from skills import market_portfolio_audit_snapshot_verifier as verifier
            
            result = verifier.verify_snapshot_integrity(self.snapshot_id)
            
            self.assertTrue(result)
            mock_db.get_snapshot.assert_called_once_with(self.snapshot_id)

    def test_verify_snapshot_corruption_detected(self):
        corrupted_hash = uuid.uuid4().hex
        mock_db = MagicMock()
        mock_db.get_snapshot.return_value = {
            "snapshot_id": self.snapshot_id,
            "portfolio_id": self.portfolio_id,
            "integrity_hash": self.expected_hash,
            "status": "CORRUPTED"
        }

        with patch.dict(sys.modules, {'db_storage': mock_db}):
            from skills import market_portfolio_audit_snapshot_verifier as verifier
            
            result = verifier.verify_snapshot_integrity(self.snapshot_id)
            
            self.assertFalse(result)

    def test_verify_snapshot_missing_data(self):
        mock_db = MagicMock()
        mock_db.get_snapshot.return_value = None

        with patch.dict(sys.modules, {'db_storage': mock_db}):
            from skills import market_portfolio_audit_snapshot_verifier as verifier
            
            result = verifier.verify_snapshot_integrity(self.snapshot_id)
            
            self.assertFalse(result)

    def test_audit_batch_snapshots(self):
        snapshots = [
            {"snapshot_id": f"snap_{uuid.uuid4().hex}", "status": "OK"},
            {"snapshot_id": f"snap_{uuid.uuid4().hex}", "status": "FAILED"}
        ]
        
        mock_db = MagicMock()
        mock_db.get_all_snapshots.return_value = snapshots

        with patch.dict(sys.modules, {'db_storage': mock_db}):
            from skills import market_portfolio_audit_snapshot_verifier as verifier
            
            audit_report = verifier.audit_batch_snapshots()
            
            self.assertIn("total", audit_report)
            self.assertEqual(audit_report["total"], 2)
            self.assertEqual(audit_report["failed"], 1)

    def test_stream_snapshot_verification_with_io(self):
        random_bytes = b"".join(random.choices([b'0', b'1', b'A', b'F'], k=64))
        stream_mock = io.BytesIO(random_bytes)
        
        mock_db = MagicMock()
        mock_db.get_raw_stream.return_value = stream_mock

        with patch.dict(sys.modules, {'db_storage': mock_db}):
            from skills import market_portfolio_audit_snapshot_verifier as verifier
            
            checksum = verifier.calculate_stream_checksum(self.snapshot_id)
            self.assertIsInstance(checksum, str)
            self.assertTrue(len(checksum) > 0)

if __name__ == '__main__':
    unittest.main()