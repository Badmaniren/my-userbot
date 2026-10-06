import unittest
import uuid
import random
import json
from skills.market_portfolio_audit_integrity_validator import validate_and_store_report
from skills.market_report_generator import generate_market_report
from skills.db_storage import fetch_stored_report

class TestMarketPortfolioAuditIntegrityValidatorIntegration(unittest.TestCase):

    def test_integrity_validator_end_to_end_flow(self):
        unique_run_id = str(uuid.uuid4())
        random_portfolio_value = round(random.uniform(10000.0, 1000000.0), 2)
        random_asset_count = random.randint(1, 50)

        raw_report = generate_market_report(
            report_id=unique_run_id,
            portfolio_value=random_portfolio_value,
            asset_count=random_asset_count
        )

        validation_result = validate_and_store_report(raw_report)

        self.assertIsInstance(validation_result, dict)
        self.assertTrue(validation_result.get("success"), f"Validation and storage failed: {validation_result}")
        self.assertEqual(validation_result.get("stored_id"), unique_run_id)

        persisted_data = fetch_stored_report(unique_run_id)

        self.assertIsNotNone(persisted_data, "Report was not found in db_storage after validation pass.")
        self.assertEqual(persisted_data["report_id"], unique_run_id)
        self.assertEqual(persisted_data["portfolio_value"], random_portfolio_value)
        self.assertEqual(persisted_data["asset_count"], random_asset_count)
        self.assertTrue(persisted_data.get("checksum_verified"))

    def test_integrity_validator_rejects_corrupted_data(self):
        corrupted_run_id = str(uuid.uuid4())
        corrupted_payload = {
            "report_id": corrupted_run_id,
            "portfolio_value": "INVALID_TYPE_VALUE",
            "asset_count": -999,
            "checksum": "deadbeef"
        }

        validation_result = validate_and_store_report(corrupted_payload)

        self.assertIsInstance(validation_result, dict)
        self.assertFalse(validation_result.get("success"), "Validator should have failed on corrupted schema.")
        self.assertIn("error", validation_result)

        persisted_data = fetch_stored_report(corrupted_run_id)
        self.assertIsNone(persisted_data, "Corrupted report must not be persisted into db_storage.")

if __name__ == "__main__":
    unittest.main()