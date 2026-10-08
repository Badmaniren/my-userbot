import os
import json
import tempfile
import unittest
from skills.db_storage import MarketParser
from skills.market_portfolio_audit_log_exporter import PortfolioAuditLogExporter
from skills.market_portfolio_audit_snapshot_verifier import (
    MarketPortfolioAuditSnapshotVerifier,
    market_portfolio_audit_snapshot_verifier,
)


class TestMarketPortfolioAuditSnapshotVerifierIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, "audit_storage.json")
        self.export_file = os.path.join(self.temp_dir.name, "exported_audit.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_integration_with_db_storage_and_log_exporter(self):
        verifier = MarketPortfolioAuditSnapshotVerifier(storage_file=self.storage_file)
        snapshot_data = {
            "snapshot_id": "snap_integ_001",
            "portfolio_id": "port_integ_100",
            "timestamp": 1700000000,
            "assets": [
                {"ticker": "BTC", "quantity": 1.5, "price": 40000.0},
                {"ticker": "ETH", "quantity": 10.0, "price": 2200.0},
            ],
        }
        snapshot_data["checksum"] = verifier.calculate_snapshot_checksum(snapshot_data)

        # Write data to storage file
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump([snapshot_data], f)

        # Verify using storage loading
        result = verifier.verify_snapshot_integrity(self.storage_file)
        self.assertEqual(result["verification_status"], "VALID")
        self.assertEqual(result["snapshot_id"], "snap_integ_001")
        self.assertEqual(result["portfolio_id"], "port_integ_100")

        # Verify export integration with PortfolioAuditLogExporter
        exporter = PortfolioAuditLogExporter(storage_file=self.storage_file)
        self.assertTrue(exporter.verify_log_integrity())
        export_success = exporter.export_audit_logs(self.export_file)
        self.assertTrue(export_success)
        self.assertTrue(os.path.exists(self.export_file))

    def test_integration_via_entry_point_with_storage_file(self):
        verifier = MarketPortfolioAuditSnapshotVerifier()
        snapshot_data = {
            "snapshot_id": "snap_integ_002",
            "portfolio_id": "port_integ_200",
            "timestamp": 1700000050,
            "assets": [{"ticker": "SOL", "quantity": 50, "price": 100.0}],
        }
        snapshot_data["checksum"] = verifier.calculate_snapshot_checksum(snapshot_data)

        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(snapshot_data, f)

        res = market_portfolio_audit_snapshot_verifier(self.storage_file, storage_file=self.storage_file)
        self.assertEqual(res["verification_status"], "VALID")
        self.assertEqual(res["snapshot_id"], "snap_integ_002")


if __name__ == "__main__":
    unittest.main()
