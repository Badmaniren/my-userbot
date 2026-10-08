import unittest
from unittest.mock import MagicMock, patch, mock_open
import io
import os
import uuid
from skills.market_portfolio_stress_audit_pdf_generator import (
    MarketPortfolioStressAuditPdfGenerator,
    market_portfolio_stress_audit_pdf_generator,
    start_new,
)


class TestMarketPortfolioStressAuditPdfGenerator(unittest.TestCase):
    def setUp(self):
        self.db_storage = MagicMock()
        self.market_report_generator = MagicMock()
        self.dummy_dependencies = [MagicMock(spec=[]) for _ in range(60)]

    def test_start_new_success_with_kwargs(self):
        random_audit_id = f"audit-{uuid.uuid4()}"
        self.db_storage.fetch_audit_data.return_value = {
            "audit_id": random_audit_id,
            "status": "PASSED",
        }
        random_binary = b"%PDF-1.4 mock content"
        self.market_report_generator.generate_pdf.return_value = random_binary

        m = mock_open()
        with patch("builtins.open", m):
            result_path = start_new(
                db_storage=self.db_storage,
                market_report_generator=self.market_report_generator,
            )

            expected_path = f"/tmp/{random_audit_id}.pdf"
            self.assertEqual(result_path, expected_path)
            m.assert_called_once_with(expected_path, "wb")
            handle = m()
            handle.write.assert_called_once_with(random_binary)

    def test_start_new_success_with_positional_args(self):
        random_audit_id = f"audit-{uuid.uuid4()}"
        audit_data = {"audit_id": random_audit_id, "score": 98.5}
        self.db_storage.fetch_audit_data.return_value = audit_data
        random_binary = b"%PDF-1.4 positional mock"
        self.market_report_generator.generate_pdf.return_value = random_binary

        m = mock_open()
        with patch("builtins.open", m):
            result_path = start_new(
                self.db_storage,
                *self.dummy_dependencies[:52],
                self.market_report_generator,
                *self.dummy_dependencies[53:]
            )

            expected_path = f"/tmp/{random_audit_id}.pdf"
            self.assertEqual(result_path, expected_path)
            m.assert_called_once_with(expected_path, "wb")
            handle = m()
            handle.write.assert_called_once_with(random_binary)
            self.db_storage.fetch_audit_data.assert_called_once()

    def test_start_new_missing_audit_data_raises_value_error(self):
        self.db_storage.fetch_audit_data.return_value = None

        with self.assertRaises(ValueError) as ctx:
            start_new(
                db_storage=self.db_storage,
                market_report_generator=self.market_report_generator,
            )

        self.assertEqual(str(ctx.exception), "Audit data is missing")

    def test_start_new_default_report_name(self):
        self.db_storage.fetch_audit_data.return_value = {"other_field": "no_id_here"}
        random_binary = b"pdf content"
        self.market_report_generator.generate_pdf.return_value = random_binary

        m = mock_open()
        with patch("builtins.open", m):
            result_path = start_new(
                db_storage=self.db_storage,
                market_report_generator=self.market_report_generator,
            )

            expected_path = "/tmp/report.pdf"
            self.assertEqual(result_path, expected_path)
            m.assert_called_once_with(expected_path, "wb")

    def test_class_generate_pdf(self):
        gen = MarketPortfolioStressAuditPdfGenerator(
            db_storage=self.db_storage,
            market_report_generator=self.market_report_generator,
        )
        payload = {"audit_id": "test_123", "value": 100}
        self.market_report_generator.generate_pdf.return_value = b"binary_data"

        m = mock_open()
        with patch("builtins.open", m):
            res = gen.generate_pdf(payload)
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["audit_id"], "test_123")
            self.assertEqual(res["pdf_path"], "/tmp/test_123.pdf")

    def test_class_generate_pdf_type_error(self):
        gen = MarketPortfolioStressAuditPdfGenerator()
        with self.assertRaises(TypeError):
            gen.generate_pdf("invalid_string_payload")

    def test_entry_point_function(self):
        payload = {"audit_id": "fn_audit_456"}
        m = mock_open()
        with patch("builtins.open", m):
            res = market_portfolio_stress_audit_pdf_generator(payload)
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["audit_id"], "fn_audit_456")


if __name__ == "__main__":
    unittest.main()
