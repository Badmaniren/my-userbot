import unittest
import os
import uuid
from skills.market_portfolio_stress_audit_pdf_generator import (
    start_new,
    MarketPortfolioStressAuditPdfGenerator,
    market_portfolio_stress_audit_pdf_generator,
)


class RealDbStorage:
    def __init__(self, audit_id):
        self.audit_id = audit_id

    def fetch_audit_data(self):
        return {
            "audit_id": self.audit_id,
            "stress_test_result": "PASSED",
            "portfolio_value": 100000.0,
        }


class RealMarketReportGenerator:
    def generate_pdf(self, audit_data):
        return f"%PDF-1.4 Content for audit {audit_data.get('audit_id')}".encode("utf-8")


class TestMarketPortfolioStressAuditPdfGeneratorIntegration(unittest.TestCase):
    def test_start_new_integration_generates_pdf_file(self):
        random_audit_id = f"audit-{uuid.uuid4()}"
        db_storage = RealDbStorage(random_audit_id)
        market_report_generator = RealMarketReportGenerator()

        expected_file_path = f"/tmp/{random_audit_id}.pdf"
        if os.path.exists(expected_file_path):
            os.remove(expected_file_path)

        try:
            result_path = start_new(
                db_storage=db_storage,
                market_report_generator=market_report_generator,
            )

            self.assertEqual(result_path, expected_file_path)
            self.assertTrue(os.path.exists(result_path))

            with open(result_path, "rb") as f:
                content = f.read()
                self.assertIn(random_audit_id.encode("utf-8"), content)
        finally:
            if os.path.exists(expected_file_path):
                os.remove(expected_file_path)

    def test_class_integration_generates_pdf_file(self):
        random_audit_id = f"audit-cls-{uuid.uuid4()}"
        db_storage = RealDbStorage(random_audit_id)
        market_report_generator = RealMarketReportGenerator()

        generator = MarketPortfolioStressAuditPdfGenerator(
            db_storage=db_storage,
            market_report_generator=market_report_generator,
        )

        expected_file_path = f"/tmp/{random_audit_id}.pdf"
        if os.path.exists(expected_file_path):
            os.remove(expected_file_path)

        try:
            result = generator.generate_pdf()
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["pdf_path"], expected_file_path)
            self.assertTrue(os.path.exists(expected_file_path))

            with open(expected_file_path, "rb") as f:
                content = f.read()
                self.assertIn(random_audit_id.encode("utf-8"), content)
        finally:
            if os.path.exists(expected_file_path):
                os.remove(expected_file_path)

    def test_entry_point_integration(self):
        random_audit_id = f"audit-ep-{uuid.uuid4()}"
        payload = {"audit_id": random_audit_id, "score": 100}

        expected_file_path = f"/tmp/{random_audit_id}.pdf"
        if os.path.exists(expected_file_path):
            os.remove(expected_file_path)

        try:
            result = market_portfolio_stress_audit_pdf_generator(payload)
            self.assertEqual(result["status"], "success")
            self.assertTrue(os.path.exists(expected_file_path))
        finally:
            if os.path.exists(expected_file_path):
                os.remove(expected_file_path)


if __name__ == "__main__":
    unittest.main()
