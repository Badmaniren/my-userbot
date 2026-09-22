import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import os

from skills.market_portfolio_audit_compliance_hub import (
    MarketPortfolioAuditComplianceHub
)

class TestMarketPortfolioAuditComplianceHub(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.export_path = f"{uuid.uuid4().hex}_{uuid.uuid4().hex}.json"
        self.hub = MarketPortfolioAuditComplianceHub(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass
        if os.path.exists(self.export_path):
            try:
                os.remove(self.export_path)
            except OSError:
                pass

    def test_init_and_composition(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        rand_price = round(random.uniform(10.0, 1000.0), 2)

        with patch('skills.market_portfolio_audit_compliance_hub.MarketParser') as mock_parser_cls, \
             patch('skills.market_portfolio_audit_compliance_hub.PortfolioAuditLogExporter') as mock_exporter_cls:
            
            mock_parser_instance = mock_parser_cls.return_value
            mock_exporter_instance = mock_exporter_cls.return_value

            hub = MarketPortfolioAuditComplianceHub(self.storage_file)
            hub.db_storage.fetch_and_store(rand_symbol, rand_price)

            mock_parser_cls.assert_called_once_with(self.storage_file)
            mock_exporter_cls.assert_called_once_with(self.storage_file)
            mock_parser_instance.fetch_and_store.assert_called_once_with(rand_symbol, rand_price)

    def test_audit_compliance_export_and_verify(self):
        expected_export_result = random.choice([True, False])
        expected_integrity_result = random.choice([True, False])
        
        rand_summary_key = uuid.uuid4().hex
        rand_summary_val = uuid.uuid4().hex
        expected_summary = {rand_summary_key: rand_summary_val}

        with patch('skills.market_portfolio_audit_compliance_hub.PortfolioAuditLogExporter') as mock_exporter_cls:
            mock_exporter_instance = mock_exporter_cls.return_value
            mock_exporter_instance.export_audit_logs.return_value = expected_export_result
            mock_exporter_instance.verify_log_integrity.return_value = expected_integrity_result
            mock_exporter_instance.get_audit_stream_summary.return_value = expected_summary

            hub = MarketPortfolioAuditComplianceHub(self.storage_file)
            
            res_export = hub.run_compliance_export(self.export_path)
            self.assertEqual(res_export, expected_export_result)
            mock_exporter_instance.export_audit_logs.assert_called_once_with(self.export_path)

            res_integrity = hub.check_compliance_integrity()
            self.assertEqual(res_integrity, expected_integrity_result)
            mock_exporter_instance.verify_log_integrity.assert_called_once()

            res_summary = hub.fetch_compliance_summary()
            self.assertEqual(res_summary, expected_summary)
            mock_exporter_instance.get_audit_stream_summary.assert_called_once()

    def test_stream_processing_and_generation_with_io(self):
        rand_bytes_content = uuid.uuid4().bytes + uuid.uuid4().bytes
        mock_stream = io.BytesIO(rand_bytes_content)

        with patch('skills.market_portfolio_audit_compliance_hub.PortfolioAuditLogExporter') as mock_exporter_cls:
            mock_exporter_instance = mock_exporter_cls.return_value
            
            hub = MarketPortfolioAuditComplianceHub(self.storage_file)
            hub.process_audit_stream_data(self.export_path, mock_stream)

            mock_exporter_instance.process_audit_stream.assert_called_once()
            
            hub.generate_compliance_log(self.export_path)
            mock_exporter_instance.generate_audit_log.assert_called_once_with(self.export_path)

    def test_market_price_fetching_integration(self):
        rand_url = f"https://{uuid.uuid4().hex}.com/market"
        rand_price = round(random.uniform(50.0, 5000.0), 2)

        with patch('skills.market_portfolio_audit_compliance_hub.MarketParser') as mock_parser_cls:
            mock_parser_instance = mock_parser_cls.return_value
            mock_parser_instance.fetch_price.return_value = rand_price

            hub = MarketPortfolioAuditComplianceHub(self.storage_file)
            price = hub.audit_fetch_market_price(rand_url)

            self.assertEqual(price, rand_price)
            mock_parser_instance.fetch_price.assert_called_once_with(rand_url)

    def test_load_audit_data_from_storage(self):
        rand_filename = f"{uuid.uuid4().hex}.json"
        rand_data = [{"audit_id": uuid.uuid4().hex, "timestamp": random.randint(100000, 999999)}]

        with patch('skills.market_portfolio_audit_compliance_hub.MarketParser') as mock_parser_cls:
            mock_parser_instance = mock_parser_cls.return_value
            mock_parser_instance.load_data.return_value = rand_data

            hub = MarketPortfolioAuditComplianceHub(self.storage_file)
            loaded = hub.load_historical_audit_data(rand_filename)

            self.assertEqual(loaded, rand_data)
            mock_parser_instance.load_data.assert_called_once_with(rand_filename)

if __name__ == '__main__':
    unittest.main()