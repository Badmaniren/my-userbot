import unittest
import os
import uuid
import json
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub
from skills.db_storage import MarketParser
from skills.market_portfolio_audit_log_exporter import PortfolioAuditLogExporter

class TestMarketPortfolioAuditComplianceHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_id = str(uuid.uuid4())
        self.storage_file = f"test_storage_{self.test_id}.json"
        self.export_path = f"audit_log_{self.test_id}.json"
        
        self.db_storage = MarketParser(self.storage_file)
        self.audit_exporter = PortfolioAuditLogExporter(self.storage_file)
        self.hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            db_storage=self.db_storage,
            audit_exporter=self.audit_exporter
        )

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.export_path):
            os.remove(self.export_path)

    def test_full_audit_lifecycle_integration(self):
        # 1. Test Data Processing
        stream_data = {"event_id": self.test_id, "status": "verified"}
        process_result = self.hub.process_audit_stream_data(self.export_path, stream_data)
        self.assertTrue(process_result)
        
        # 2. Test Log Generation
        gen_result = self.hub.generate_compliance_log(self.export_path)
        self.assertTrue(gen_result)
        self.assertTrue(os.path.exists(self.export_path))

        # 3. Test Integrity Verification
        integrity = self.hub.check_compliance_integrity()
        self.assertTrue(integrity)

        # 4. Test Export Functionality
        export_status = self.hub.run_compliance_export(self.export_path)
        self.assertTrue(export_status)

        # 5. Verify data persistence in file
        with open(self.export_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(self.test_id, content)

    def test_market_price_fetch_integration(self):
        # Проверка реального взаимодействия с хранилищем через хаб
        test_url = f"https://api.test.com/{self.test_id}"
        # В реальной системе MarketParser должен вернуть данные или None
        # Проверяем, что вызов проходит без исключений и возвращает ожидаемый тип
        result = self.hub.audit_fetch_market_price(test_url)
        self.assertIsNotNone(result)

    def test_summary_consistency(self):
        # Проверка согласованности данных между методами
        summary = self.hub.get_audit_stream_summary()
        self.assertIsInstance(summary, (dict, list, bool))

if __name__ == '__main__':
    unittest.main()