import unittest
import uuid
import random
import os

from skills.market_portfolio_stress_audit_exporter_v2 import (
    market_portfolio_stress_audit_exporter_v2_main
)

class TestMarketPortfolioStressAuditExporterV2Integration(unittest.TestCase):

    def test_export_stress_audit_report_real_flow(self):
        unique_run_id = str(uuid.uuid4())
        portfolio_id = f"port_{random.randint(10000, 99999)}"
        stress_level = round(random.uniform(0.1, 0.9), 4)
        
        test_payload = {
            "run_id": unique_run_id,
            "portfolio_id": portfolio_id,
            "stress_factor": stress_level,
            "export_format": "json",
            "strict_anti_cheat": True
        }

        result = market_portfolio_stress_audit_exporter_v2_main(test_payload)

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertEqual(result.get("run_id"), unique_run_id)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        
        if "export_path" in result and result["export_path"]:
            path = result["export_path"]
            self.assertTrue(os.path.exists(path), f"Экспортированный файл не найден по пути: {path}")
            
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn(unique_run_id, content)
                
            if os.path.exists(path):
                os.remove(path)

if __name__ == "__main__":
    unittest.main()