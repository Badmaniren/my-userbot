import unittest
from unittest.mock import MagicMock, patch
import os
import uuid
import random
import io
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub

class TestMarketPortfolioAuditComplianceHub(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.mock_db_storage = MagicMock()
        self.mock_audit_exporter = MagicMock()
        self.hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            db_storage=self.mock_db_storage,
            audit_exporter=self.mock_audit_exporter
        )

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_run_compliance_export_success(self):
        expected_result = random.choice([True, {"status": uuid.uuid4().hex}])
        self.mock_audit_exporter.export_audit_logs.return_value = expected_result
        export_path = f"{uuid.uuid4().hex}.log"

        result = self.hub.run_compliance_export(export_path)

        self.assertEqual(result, expected_result)
        self.mock_audit_exporter.export_audit_logs.assert_called_once_with(export_path)

    def test_run_compliance_export_fallback_creation(self):
        self.mock_audit_exporter.export_audit_logs.return_value = False
        export_path = f"{uuid.uuid4().hex}.json"

        try:
            result = self.hub.run_compliance_export(export_path)
            self.assertTrue(result)
            self.assertTrue(os.path.exists(export_path))
            with open(export_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertEqual(content, "{}")
        finally:
            if os.path.exists(export_path):
                os.remove(export_path)

    def test_check_compliance_integrity_none_to_true(self):
        self.mock_audit_exporter.verify_log_integrity.return_value = None

        result = self.hub.check_compliance_integrity()

        self.assertTrue(result)
        self.mock_audit_exporter.verify_log_integrity.assert_called_once()

    def test_check_compliance_integrity_explicit_value(self):
        expected = random.choice([True, False])
        self.mock_audit_exporter.verify_log_integrity.return_value = expected

        result = self.hub.check_compliance_integrity()

        self.assertEqual(result, expected)

    def test_fetch_compliance_summary(self):
        expected_summary = {uuid.uuid4().hex: random.randint(1, 100)}
        self.mock_audit_exporter.get_audit_stream_summary.return_value = expected_summary

        result = self.hub.fetch_compliance_summary()

        self.assertEqual(result, expected_summary)
        self.mock_audit_exporter.get_audit_stream_summary.assert_called_once()

    def test_process_audit_stream_data(self):
        export_path = f"{uuid.uuid4().hex}.log"
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        self.mock_audit_exporter.process_audit_stream.return_value = None

        result = self.hub.process_audit_stream_data(export_path, stream_data)

        self.assertTrue(result)
        self.mock_audit_exporter.process_audit_stream.assert_called_once_with(export_path, stream_data)

    def test_generate_compliance_log(self):
        export_path = f"{uuid.uuid4().hex}.log"
        self.mock_audit_exporter.generate_audit_log.return_value = None

        result = self.hub.generate_compliance_log(export_path)

        self.assertTrue(result)
        self.mock_audit_exporter.generate_audit_log.assert_called_once_with(export_path)

    def test_audit_fetch_market_price_success(self):
        url = f"https://{uuid.uuid4().hex}.com/price"
        expected_price = round(random.uniform(10.0, 1000.0), 2)
        self.mock_db_storage.fetch_price.return_value = expected_price

        result = self.hub.audit_fetch_market_price(url)

        self.assertEqual(result, expected_price)
        self.mock_db_storage.fetch_price.assert_called_once_with(url)

    def test_audit_fetch_market_price_exception(self):
        url = f"https://{uuid.uuid4().hex}.com/error"
        self.mock_db_storage.fetch_price.side_effect = Exception(uuid.uuid4().hex)

        result = self.hub.audit_fetch_market_price(url)

        self.assertEqual(result, 0.0)

    def test_load_historical_audit_data_existing_file(self):
        filename = f"{uuid.uuid4().hex}.json"
        expected_data = [{"id": uuid.uuid4().hex}]
        self.mock_db_storage.load_data.return_value = expected_data

        with open(filename, "w", encoding="utf-8") as f:
            f.write("[]")

        try:
            result = self.hub.load_historical_audit_data(filename)
            self.assertEqual(result, expected_data)
            self.mock_db_storage.load_data.assert_called_once_with(filename)
        finally:
            if os.path.exists(filename):
                os.remove(filename)

    def test_load_historical_audit_data_missing_file(self):
        filename = f"{uuid.uuid4().hex}.json"
        expected_data = []
        self.mock_db_storage.load_data.return_value = expected_data

        if os.path.exists(filename):
            os.remove(filename)

        try:
            result = self.hub.load_historical_audit_data(filename)
            self.assertEqual(result, expected_data)
            self.assertTrue(os.path.exists(filename))
            with open(filename, "r", encoding="utf-8") as f:
                self.assertEqual(f.read(), "[]")
        finally:
            if os.path.exists(filename):
                os.remove(filename)

    def test_get_audit_stream_summary(self):
        expected = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_audit_exporter.get_audit_stream_summary.return_value = expected

        res = self.hub.get_audit_stream_summary()
        self.assertEqual(res, expected)

    def test_verify_log_integrity(self):
        self.mock_audit_exporter.verify_log_integrity.return_value = None
        res = self.hub.verify_log_integrity()
        self.assertTrue(res)

    def test_export_audit_logs(self):
        export_path = f"{uuid.uuid4().hex}.json"
        self.mock_audit_exporter.export_audit_logs.return_value = False
        try:
            res = self.hub.export_audit_logs(export_path)
            self.assertTrue(res)
            self.assertTrue(os.path.exists(export_path))
        finally:
            if os.path.exists(export_path):
                os.remove(export_path)

if __name__ == '__main__':
    unittest.main()