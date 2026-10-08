import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
from skills.market_portfolio_stress_audit_pdf_exporter import start_new

class TestMarketPortfolioStressAuditPdfExporter(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.market_report_generator = MagicMock()
        self.dummy_dependencies = [MagicMock() for _ in range(58)]

    def test_start_new_success(self):
        audit_id_str = uuid.uuid4().hex
        random_binary = bytes(random.getrandbits(8) for _ in range(64))
        
        self.db_storage.fetch_audit_data.return_value = {"audit_id": audit_id_str, "data": uuid.uuid4().hex}
        self.market_report_generator.generate_pdf.return_value = random_binary

        mock_file = MagicMock()
        
        with patch("builtins.open", return_value=mock_file.__enter__()) as mock_open:
            result_path = start_new(
                self.db_storage,
                *self.dummy_dependencies[:4],
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                self.market_report_generator,
                *self.dummy_dependencies[49:]
            )

            expected_path = f"/tmp/{audit_id_str}.pdf"
            self.assertEqual(result_path, expected_path)
            mock_open.assert_called_once_with(expected_path, "wb")
            mock_file.__enter__().write.assert_called_once_with(random_binary)
            self.db_storage.fetch_audit_data.assert_called_once()
            self.market_report_generator.generate_pdf.assert_called_once()

    def test_start_new_missing_audit_data(self):
        self.db_storage.fetch_audit_data.return_value = None

        with self.assertRaises(ValueError) as ctx:
            start_new(
                self.db_storage,
                *self.dummy_dependencies[:4],
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                self.market_report_generator,
                *self.dummy_dependencies[49:]
            )

        self.assertEqual(str(ctx.exception), "Audit data is missing")
        self.db_storage.fetch_audit_data.assert_called_once()
        self.market_report_generator.generate_pdf.assert_not_called()

    def test_start_new_default_report_name(self):
        random_id = uuid.uuid4().hex
        self.db_storage.fetch_audit_data.return_value = {"other_field": random_id}
        random_binary = io.BytesIO(b"some random pdf stream content").read()
        self.market_report_generator.generate_pdf.return_value = random_binary

        mock_file = MagicMock()

        with patch("builtins.open", return_value=mock_file.__enter__()) as mock_open:
            result_path = start_new(
                self.db_storage,
                *self.dummy_dependencies[:4],
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                self.market_report_generator,
                *self.dummy_dependencies[49:]
            )

            expected_path = "/tmp/report.pdf"
            self.assertEqual(result_path, expected_path)
            mock_open.assert_called_once_with(expected_path, "wb")
            mock_file.__enter__().write.assert_called_once_with(random_binary)

if __name__ == "__main__":
    unittest.main()