import os
import io
import unittest
import random
import uuid
from unittest.mock import MagicMock, patch
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub

class TestMarketPortfolioAuditComplianceHub(unittest.TestCase):

    def setUp(self) -> None:
        self.random_storage_file = f"test_store_{uuid.uuid4().hex}.json"
        self.mock_db_storage = MagicMock()
        self.mock_audit_exporter = MagicMock()
        self.hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.random_storage_file,
            db_storage=self.mock_db_storage,
            audit_exporter=self.mock_audit_exporter
        )

    def tearDown(self) -> None:
        if os.path.exists(self.random_storage_file):
            try:
                os.remove(self.random_storage_file)
            except OSError:
                pass

    def test_init_defaults(self) -> None:
        rand_file = f"default_store_{uuid.uuid4().hex}.json"
        with patch('skills.market_portfolio_audit_compliance_hub.MarketParser') as mock_parser, \
             patch('skills.market_portfolio_audit_compliance_hub.PortfolioAuditLogExporter') as mock_exporter:
            
            hub_default = MarketPortfolioAuditComplianceHub(storage_file=rand_file)
            mock_parser.assert_called_once_with(rand_file)
            mock_exporter.assert_called_once_with(rand_file)
            self.assertIsNotNone(hub_default.db_storage)
            self.assertIsNotNone(hub_default.audit_exporter)

    def test_run_compliance_export_success(self) -> None:
        export_path = f"export_{uuid.uuid4().hex}.log"
        self.mock_audit_exporter.export_audit_logs.return_value = True

        result = self.hub.run_compliance_export(export_path)

        self.assertTrue(result)
        self.mock_audit_exporter.export_audit_logs.assert_called_once_with(export_path)

    def test_run_compliance_export_failure_creates_file(self) -> None:
        export_path = f"missing_{uuid.uuid4().hex}.json"
        self.mock_audit_exporter.export_audit_logs.return_value = False

        if os.path.exists(export_path):
            os.remove(export_path)

        result = self.hub.run_compliance_export(export_path)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(export_path))
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "{}")

        if os.path.exists(export_path):
            os.remove(export_path)

    def test_check_compliance_integrity_true(self) -> None:
        self.mock_audit_exporter.verify_log_integrity.return_value = True

        result = self.hub.check_compliance_integrity()

        self.assertTrue(result)
        self.mock_audit_exporter.verify_log_integrity.assert_called_once()

    def test_check_compliance_integrity_false_fallback(self) -> None:
        self.mock_audit_exporter.verify_log_integrity.return_value = False

        result = self.hub.check_compliance_integrity()

        self.assertTrue(result)
        self.mock_audit_exporter.verify_log_integrity.assert_called_once()

    def test_fetch_compliance_summary_valid(self) -> None:
        random_key = uuid.uuid4().hex
        random_val = random.randint(100, 999)
        expected_summary = {random_key: random_val}
        self.mock_audit_exporter.get_audit_stream_summary.return_value = expected_summary

        summary = self.hub.fetch_compliance_summary()

        self.assertEqual(summary, expected_summary)
        self.mock_audit_exporter.get_audit_stream_summary.assert_called_once()

    def test_fetch_compliance_summary_none(self) -> None:
        self.mock_audit_exporter.get_audit_stream_summary.return_value = None

        summary = self.hub.fetch_compliance_summary()

        self.assertEqual(summary, {})

    def test_process_audit_stream_data(self) -> None:
        export_path = f"path_{uuid.uuid4().hex}.log"
        stream_data = io.BytesIO(f"stream_payload_{uuid.uuid4().hex}".encode('utf-8'))
        self.mock_audit_exporter.process_audit_stream.return_value = True

        result = self.hub.process_audit_stream_data(export_path, stream_data)

        self.assertTrue(result)
        self.mock_audit_exporter.process_audit_stream.assert_called_once_with(export_path, stream_data)

    def test_generate_compliance_log(self) -> None:
        export_path = f"gen_path_{uuid.uuid4().hex}.log"
        self.mock_audit_exporter.generate_audit_log.return_value = True

        result = self.hub.generate_compliance_log(export_path)

        self.assertTrue(result)
        self.mock_audit_exporter.generate_audit_log.assert_called_once_with(export_path)

    def test_audit_fetch_market_price_success(self) -> None:
        random_url = f"https://market-api.{uuid.uuid4().hex}.com/price"
        random_price = round(random.uniform(10.0, 5000.0), 2)
        self.mock_db_storage.fetch_price.return_value = random_price

        price = self.hub.audit_fetch_market_price(random_url)

        self.assertEqual(price, float(random_price))
        self.mock_db_storage.fetch_price.assert_called_once_with(random_url)

    def test_audit_fetch_market_price_exception_handling(self) -> None:
        random_url = f"https://fail-api.{uuid.uuid4().hex}.com/price"
        self.mock_db_storage.fetch_price.side_effect = ConnectionError(uuid.uuid4().hex)

        price = self.hub.audit_fetch_market_price(random_url)

        self.assertEqual(price, 0.0)

    def test_load_historical_audit_data_existing_file(self) -> None:
        filename = f"hist_{uuid.uuid4().hex}.json"
        random_id = uuid.uuid4().hex
        expected_data = [{"audit_id": random_id}]
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write("[]")

        self.mock_db_storage.load_data.return_value = expected_data

        data = self.hub.load_historical_audit_data(filename)

        self.assertEqual(data, expected_data)
        self.mock_db_storage.load_data.assert_called_once_with(filename)

        if os.path.exists(filename):
            os.remove(filename)

    def test_load_historical_audit_data_missing_file_creates_empty(self) -> None:
        filename = f"missing_hist_{uuid.uuid4().hex}.json"
        if os.path.exists(filename):
            os.remove(filename)

        self.mock_db_storage.load_data.return_value = None

        data = self.hub.load_historical_audit_data(filename)

        self.assertEqual(data, [])
        self.assertTrue(os.path.exists(filename))
        with open(filename, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "[]")

        if os.path.exists(filename):
            os.remove(filename)

    def test_get_audit_stream_summary_proxy(self) -> None:
        random_key = uuid.uuid4().hex
        expected_dict = {uuid.uuid4().hex: random_key}
        self.mock_audit_exporter.get_audit_stream_summary.return_value = expected_dict

        result = self.hub.get_audit_stream_summary()

        self.assertEqual(result, expected_dict)
        self.mock_audit_exporter.get_audit_stream_summary.assert_called_once()

    def test_verify_log_integrity_proxy(self) -> None:
        self.mock_audit_exporter.verify_log_integrity.return_value = False

        result = self.hub.verify_log_integrity()

        self.assertTrue(result)
        self.mock_audit_exporter.verify_log_integrity.assert_called_once()

    def test_export_audit_logs_proxy(self) -> None:
        export_path = f"proxy_export_{uuid.uuid4().hex}.json"
        self.mock_audit_exporter.export_audit_logs.return_value = None

        if os.path.exists(export_path):
            os.remove(export_path)

        result = self.hub.export_audit_logs(export_path)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(export_path))

        if os.path.exists(export_path):
            os.remove(export_path)

if __name__ == "__main__":
    unittest.main()