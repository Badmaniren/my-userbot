import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.market_portfolio_regulatory_reporting_feed import MarketPortfolioRegulatoryReportingFeed

class TestMarketPortfolioRegulatoryReportingFeed(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.summary_vault = MagicMock()
        self.exporter_v2 = MagicMock()
        self.report_generator = MagicMock()

        self.feed = MarketPortfolioRegulatoryReportingFeed(
            db_storage=self.db_storage,
            market_portfolio_stress_audit_summary_vault=self.summary_vault,
            market_portfolio_stress_audit_exporter_v2=self.exporter_v2,
            market_report_generator=self.report_generator
        )

    def test_generate_regulatory_feed_success(self):
        random_report_id = uuid.uuid4().hex
        random_audit_hash = uuid.uuid4().hex
        random_payload_data = ''.join(random.choices(string.ascii_letters + string.digits, k=64))

        self.summary_vault.fetch_latest_audit_summary.return_value = {
            "audit_hash": random_audit_hash,
            "data": random_payload_data
        }

        self.exporter_v2.export_v2_format.return_value = {
            "status": "EXPORTED",
            "reference_id": random_report_id
        }

        with patch("skills.market_portfolio_regulatory_reporting_feed.datetime") as mock_dt:
            mock_dt.utcnow.return_value.isoformat.return_value = uuid.uuid4().hex

            result = self.feed.generate_feed(report_id=random_report_id)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("report_id"), random_report_id)
        self.assertEqual(result.get("audit_reference"), random_audit_hash)
        self.assertTrue(self.summary_vault.fetch_latest_audit_summary.called)
        self.assertTrue(self.exporter_v2.export_v2_format.called)
        self.db_storage.save_regulatory_feed_log.assert_called_once()

    def test_generate_regulatory_feed_vault_missing_data(self):
        random_missing_id = uuid.uuid4().hex
        self.summary_vault.fetch_latest_audit_summary.return_value = None

        with self.assertRaises(ValueError):
            self.feed.generate_feed(report_id=random_missing_id)

        self.assertFalse(self.exporter_v2.export_v2_format.called)
        self.db_storage.save_regulatory_feed_log.assert_not_called()

    def test_validate_regulatory_compliance_stream(self):
        random_stream_token = uuid.uuid4().hex
        random_feed_stream = io.BytesIO(random_stream_token.encode('utf-8'))

        with patch("skills.market_portfolio_regulatory_reporting_feed.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"validated": True, "token": random_stream_token}
            mock_post.return_value = mock_response

            is_valid = self.feed.validate_feed_stream(random_feed_stream)

        self.assertTrue(is_valid)
        mock_post.assert_called_once()

    def test_export_audit_regulatory_package(self):
        random_package_name = f"report_{uuid.uuid4().hex}.pdf"
        random_bytes_content = ''.join(random.choices(string.printable, k=128)).encode('utf-8')

        self.report_generator.render_pdf.return_value = io.BytesIO(random_bytes_content)

        exported_bytes = self.feed.export_regulatory_package(filename=random_package_name)

        self.assertIsInstance(exported_bytes, bytes)
        self.assertEqual(exported_bytes, random_bytes_content)
        self.report_generator.render_pdf.assert_called_once()

if __name__ == "__main__":
    unittest.main()