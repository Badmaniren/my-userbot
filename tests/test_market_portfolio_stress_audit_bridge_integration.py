import unittest
import os
import tempfile
import uuid
import random

from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub
from skills.market_portfolio_stress_audit_bridge import run_stress_audit_bridge

class TestMarketPortfolioStressAuditBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"storage_{uuid.uuid4().hex}.json")
        self.export_path = os.path.join(self.test_dir.name, f"audit_export_{uuid.uuid4().hex}.json")

        self.symbol = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(5.0, 30.0), 2)
        self.shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(3)]

        import json
        with open(self.storage_file, 'w') as f:
            json.dump({
                self.symbol: {
                    "symbol": self.symbol,
                    "current_price": 100.0,
                    "quantity": 10.0
                }
            }, f)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_stress_audit_bridge_integration(self):
        pipeline = PortfolioStressScenarioPipeline(storage_file=self.storage_file)
        compliance_hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            db_storage=None,
            audit_exporter=None
        )

        stress_result = pipeline.execute(
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertIsNotNone(stress_result)

        bridge_output = run_stress_audit_bridge(
            pipeline_instance=pipeline,
            compliance_hub_instance=compliance_hub,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts,
            export_path=self.export_path
        )

        self.assertTrue(os.path.exists(self.export_path), "Интеграционный мост должен экспортировать данные аудита в файл.")

        summary = compliance_hub.fetch_compliance_summary()
        self.assertIsNotNone(summary)

        integrity_check = compliance_hub.check_compliance_integrity()
        self.assertTrue(integrity_check)

if __name__ == "__main__":
    unittest.main()