import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string
import json
import requests

from skills.market_portfolio_stress_governance_ledger import (
    StressGovernanceLedger,
    LedgerEntry,
    ComplianceViolationError
)


class TestStressGovernanceLedger(unittest.TestCase):

    def setUp(self):
        self.rand_db_url = f"sqlite:///{uuid.uuid4().hex}.db"
        self.mock_db_storage = MagicMock()
        self.ledger = StressGovernanceLedger(db_storage=self.mock_db_storage)

    def test_record_stress_simulation_success(self):
        sim_id = uuid.uuid4().hex
        portfolio_id = uuid.uuid4().hex
        scenario_name = "".join(random.choices(string.ascii_letters, k=10))
        max_drawdown = round(random.uniform(0.05, 0.95), 4)
        var_limit = round(random.uniform(1000.0, 50000.0), 2)
        actual_var = round(var_limit * random.uniform(0.5, 0.99), 2)

        payload = {
            "simulation_id": sim_id,
            "portfolio_id": portfolio_id,
            "scenario_name": scenario_name,
            "max_drawdown": max_drawdown,
            "var_limit": var_limit,
            "actual_var": actual_var,
            "compliant": True
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "committed", "tx_hash": uuid.uuid4().hex}

        with patch("requests.post", return_value=mock_response) as mock_post:
            result = self.ledger.record_simulation(payload)
            self.assertTrue(result)
            mock_post.assert_called_once()
            self.mock_db_storage.save.assert_called_once()

    def test_record_stress_simulation_compliance_violation(self):
        sim_id = uuid.uuid4().hex
        portfolio_id = uuid.uuid4().hex
        scenario_name = "".join(random.choices(string.ascii_letters, k=12))
        var_limit = round(random.uniform(5000.0, 15000.0), 2)
        actual_var = var_limit * random.uniform(1.05, 2.0)

        payload = {
            "simulation_id": sim_id,
            "portfolio_id": portfolio_id,
            "scenario_name": scenario_name,
            "var_limit": var_limit,
            "actual_var": actual_var,
            "compliant": False
        }

        with self.assertRaises(ComplianceViolationError):
            self.ledger.record_simulation(payload)

    def test_generate_compliance_report(self):
        portfolio_id = uuid.uuid4().hex
        expected_records_count = random.randint(1, 10)

        mock_entries = []
        for _ in range(expected_records_count):
            mock_entries.append({
                "sim_id": uuid.uuid4().hex,
                "portfolio_id": portfolio_id,
                "var_limit": random.randint(1000, 5000),
                "actual_var": random.randint(500, 4500),
                "timestamp": random.randint(1600000000, 1700000000)
            })

        self.mock_db_storage.query.return_value = mock_entries

        report = self.ledger.generate_report(portfolio_id)

        self.assertIn("report_id", report)
        self.assertEqual(report["portfolio_id"], portfolio_id)
        self.assertEqual(len(report["simulations"]), expected_records_count)
        self.assertTrue(report["governance_status"])

    def test_export_ledger_stream_io(self):
        random_bytes_content = "".join(random.choices(string.printable, k=100)).encode("utf-8")
        mock_stream = io.BytesIO(random_bytes_content)

        self.mock_db_storage.stream_export.return_value = mock_stream

        export_token = uuid.uuid4().hex
        stream_result = self.ledger.export_ledger_stream(export_token)

        data = stream_result.read()
        self.assertEqual(data, random_bytes_content)

    def test_verify_integrity_hash_mismatch(self):
        target_id = uuid.uuid4().hex
        corrupted_hash = uuid.uuid4().hex

        self.mock_db_storage.get_ledger_hash.return_value = uuid.uuid4().hex

        with patch("skills.market_portfolio_stress_governance_ledger.hashlib.sha256") as mock_sha:
            mock_sha.return_value.hexdigest.return_value = corrupted_hash
            is_valid = self.ledger.verify_ledger_integrity(target_id)
            self.assertFalse(is_valid)

if __name__ == "__main__":
    unittest.main()