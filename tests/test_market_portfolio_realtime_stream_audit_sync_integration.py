import unittest
import uuid
import random
import os
from skills.market_portfolio_realtime_stream_audit_sync import (
    market_portfolio_realtime_stream_audit_sync,
    db_storage,
    market_portfolio_stress_scenario_pipeline,
    market_portfolio_realtime_stream_ingestor,
    market_portfolio_stress_audit_realtime_streamer,
    market_portfolio_audit_compliance_hub
)

class TestMarketPortfolioRealtimeStreamAuditSyncIntegration(unittest.TestCase):
    def test_realtime_stream_audit_sync_execution(self):
        unique_test_id = str(uuid.uuid4())
        random_market_value = round(random.uniform(1000.0, 1000000.0), 2)
        random_stress_factor = round(random.uniform(0.01, 0.5), 4)

        scenario_input = {
            "test_id": unique_test_id,
            "portfolio_value": random_market_value,
            "stress_factor": random_stress_factor,
            "mode": "realtime_audit_sync"
        }

        pipeline_result = market_portfolio_stress_scenario_pipeline(scenario_input)
        self.assertIsNotNone(pipeline_result, "Pipeline did not return data")

        ingestor_payload = {
            "id": unique_test_id,
            "stream_data": pipeline_result,
            "timestamp": uuid.uuid1().int
        }
        ingestor_result = market_portfolio_realtime_stream_ingestor(ingestor_payload)
        self.assertEqual(ingestor_result.get("status"), "ingested")

        streamer_output = market_portfolio_stress_audit_realtime_streamer(ingestor_result)
        self.assertIn("audit_stream_id", streamer_output)

        compliance_status = market_portfolio_audit_compliance_hub(streamer_output)
        self.assertTrue(compliance_status.get("compliant", False))

        sync_payload = {
            "sync_id": unique_test_id,
            "compliance_ref": compliance_status.get("ref_id"),
            "data": streamer_output
        }
        sync_result = market_portfolio_realtime_stream_audit_sync(sync_payload)
        self.assertIsNotNone(sync_result)
        self.assertEqual(sync_result.get("sync_id"), unique_test_id)

        stored_record = db_storage.get(unique_test_id)
        self.assertIsNotNone(stored_record, "Data was not persisted in db_storage")
        self.assertEqual(stored_record.get("portfolio_value"), random_market_value)

        audit_log_path = f"/var/log/audit_{unique_test_id}.log"
        if os.path.exists(audit_log_path):
            self.assertTrue(os.path.getsize(audit_log_path) > 0)

if __name__ == "__main__":
    unittest.main()