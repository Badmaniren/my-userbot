import unittest
import uuid
import os
import json
import tempfile
from skills.market_insider_investigation_dossier_builder import (
    market_insider_investigation_dossier_builder,
    start_new
)
from skills.db_storage import db_storage

class TestMarketInsiderInvestigationDossierBuilderIntegration(unittest.TestCase):
    def setUp(self):
        self.target_id = str(uuid.uuid4())
        self.anomaly_id = str(uuid.uuid4())
        self.ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_file = os.path.join(self.temp_dir.name, f"dossier_{uuid.uuid4()}.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_market_insider_investigation_dossier_builder_integration(self):
        payload = {
            "anomaly_id": self.anomaly_id,
            "ticker": self.ticker,
            "output_file": self.output_file,
            "include_history": True
        }

        result = market_insider_investigation_dossier_builder(payload)

        self.assertEqual(result.get("anomaly_id"), self.anomaly_id)
        self.assertEqual(result.get("ticker"), self.ticker)
        self.assertEqual(result.get("dossier_status"), "completed")
        self.assertTrue(result.get("include_history"))

        self.assertTrue(os.path.exists(self.output_file))

        with open(self.output_file, "r", encoding="utf-8") as f:
            file_data = json.load(f)
            self.assertEqual(file_data.get("anomaly_id"), self.anomaly_id)
            self.assertEqual(file_data.get("ticker"), self.ticker)
            self.assertEqual(file_data.get("dossier_status"), "completed")

    def test_start_new_integration_with_db_storage(self):
        kwargs = {
            "db_storage": db_storage
        }

        start_result = start_new(self.target_id, **kwargs)

        self.assertIsNotNone(start_result)
        self.assertEqual(start_result.get("target_id"), self.target_id)
        self.assertEqual(start_result.get("status"), "success")

if __name__ == "__main__":
    unittest.main()