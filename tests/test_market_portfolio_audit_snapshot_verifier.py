import unittest
from skills.market_portfolio_audit_snapshot_verifier import (
    MarketPortfolioAuditSnapshotVerifier,
    PortfolioAuditSnapshotVerifier,
    market_portfolio_audit_snapshot_verifier,
)


class TestMarketPortfolioAuditSnapshotVerifier(unittest.TestCase):

    def setUp(self):
        self.verifier = MarketPortfolioAuditSnapshotVerifier()
        self.valid_snapshot = {
            "snapshot_id": "snap_001",
            "portfolio_id": "port_123",
            "timestamp": 1690000000,
            "assets": [{"ticker": "AAPL", "quantity": 10, "price": 150.0}],
        }
        self.valid_snapshot["checksum"] = self.verifier.calculate_snapshot_checksum(self.valid_snapshot)

    def test_verify_snapshot_schema_success(self):
        self.assertTrue(self.verifier.verify_snapshot_schema(self.valid_snapshot))

    def test_verify_snapshot_schema_missing_field_raises_value_error(self):
        invalid_snapshot = self.valid_snapshot.copy()
        del invalid_snapshot["timestamp"]
        with self.assertRaises(ValueError) as ctx:
            self.verifier.verify_snapshot_schema(invalid_snapshot)
        self.assertIn("timestamp", str(ctx.exception))

    def test_verify_snapshot_schema_invalid_type(self):
        with self.assertRaises(ValueError):
            self.verifier.verify_snapshot_schema("not_a_dict")

    def test_calculate_snapshot_checksum_deterministic(self):
        cs1 = self.verifier.calculate_snapshot_checksum(self.valid_snapshot)
        cs2 = self.verifier.calculate_snapshot_checksum(self.valid_snapshot)
        self.assertEqual(cs1, cs2)

    def test_verify_snapshot_checksum_success(self):
        self.assertTrue(self.verifier.verify_snapshot_checksum(self.valid_snapshot))

    def test_verify_snapshot_checksum_mismatch_raises_value_error(self):
        tampered_snapshot = self.valid_snapshot.copy()
        tampered_snapshot["checksum"] = "0" * 64
        with self.assertRaises(ValueError) as ctx:
            self.verifier.verify_snapshot_checksum(tampered_snapshot)
        self.assertIn("Несовпадение контрольной суммы", str(ctx.exception))

    def test_verify_snapshot_checksum_missing_checksum_raises_value_error(self):
        no_cs_snapshot = {k: v for k, v in self.valid_snapshot.items() if k != "checksum"}
        with self.assertRaises(ValueError) as ctx:
            self.verifier.verify_snapshot_checksum(no_cs_snapshot)
        self.assertIn("отсутствует", str(ctx.exception))

    def test_verify_snapshot_data_valid(self):
        res = self.verifier.verify_snapshot_data(self.valid_snapshot)
        self.assertEqual(res["verification_status"], "VALID")
        self.assertEqual(res["snapshot_id"], "snap_001")
        self.assertEqual(res["portfolio_id"], "port_123")

    def test_top_level_function_entry_point(self):
        res = market_portfolio_audit_snapshot_verifier(self.valid_snapshot)
        self.assertEqual(res["verification_status"], "VALID")

    def test_class_alias(self):
        alias_verifier = PortfolioAuditSnapshotVerifier()
        self.assertTrue(alias_verifier.verify_snapshot_schema(self.valid_snapshot))


if __name__ == "__main__":
    unittest.main()
