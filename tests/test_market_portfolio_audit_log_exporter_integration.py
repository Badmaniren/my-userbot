import unittest
import os
import uuid
import random
from skills.market_portfolio_audit_log_exporter import MarketPortfolioAuditLogExporter
from skills.market_parser import MarketParser

class TestMarketPortfolioAuditLogExporterIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_audit_storage_{uuid.uuid4()}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.price = round(random.uniform(10.0, 1500.0), 2)
        
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)

    def tearDown(self):
        for fpath in [self.storage_file, self.symbol]:
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except OSError:
                    pass

    def test_audit_log_exporter_integration(self):
        exporter = MarketPortfolioAuditLogExporter(self.storage_file)
        
        self.assertTrue(
            hasattr(exporter, "export_audit_logs") or 
            hasattr(exporter, "generate_audit_log") or 
            hasattr(exporter, "process_audit_stream"),
            "Exporter must contain a valid processing method"
        )
        
        if hasattr(exporter, "export_audit_logs"):
            result = exporter.export_audit_logs(self.symbol)
        elif hasattr(exporter, "generate_audit_log"):
            result = exporter.generate_audit_log(self.symbol)
        else:
            result = exporter.process_audit_stream(self.symbol)
            
        self.assertIsNotNone(result)

if __name__ == "__main__":
    unittest.main()