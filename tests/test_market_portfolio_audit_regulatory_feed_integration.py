import unittest
import uuid
import random
import os
from skills.market_portfolio_audit_regulatory_feed import (
    market_portfolio_audit_regulatory_feed,
    db_storage,
    market_parser,
    market_portfolio_audit_compliance_hub
)

class IntegrationTestMarketPortfolioAuditRegulatoryFeed(unittest.TestCase):
    def test_regulatory_feed_end_to_end_integration(self):
        unique_feed_id = f"feed_{uuid.uuid4().hex}"
        random_regulation_code = f"REG-{random.randint(1000, 9999)}"
        test_source_url = f"https://example.com/regulatory/{uuid.uuid4().hex}"

        feed_payload = {
            "feed_id": unique_feed_id,
            "code": random_regulation_code,
            "source": test_source_url,
            "threshold": random.uniform(0.01, 0.15)
        }

        parsed_data = market_parser(feed_payload)
        self.assertIsNotNone(parsed_data)

        stored_record = db_storage(parsed_data)
        self.assertIn("id", stored_record)

        compliance_result = market_portfolio_audit_compliance_hub(stored_record)
        self.assertTrue(compliance_result.get("validated", False))

        audit_feed_output = market_portfolio_audit_regulatory_feed(compliance_result)

        self.assertIsInstance(audit_feed_output, dict)
        self.assertEqual(audit_feed_output.get("feed_id"), unique_feed_id)
        self.assertEqual(audit_feed_output.get("code"), random_regulation_code)
        self.assertTrue(audit_feed_output.get("processed", False))

        audit_file_path = f"audit_feed_{unique_feed_id}.log"
        if os.path.exists(audit_file_path):
            os.remove(audit_file_path)

if __name__ == "__main__":
    unittest.main()