import unittest
import uuid
import random
import tempfile
import os

from skills.telemetry_anomaly_evaluator_core import TelemetryAnomalyEvaluatorCore
from skills.telemetry_anomaly_response_connector import TelemetryAnomalyResponseConnector
from skills.telemetry_incident_lifecycle_bridge import (
    process_lifecycle_telemetry,
    TelemetryIncidentLifecycleBridge
)


class TestTelemetryIncidentLifecycleBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = tempfile.mkdtemp()
        self.evaluator = TelemetryAnomalyEvaluatorCore()
        self.escalation_engine = "DefaultEscalationEngine"
        self.connector = TelemetryAnomalyResponseConnector(
            workspace_dir=self.workspace_dir,
            evaluator=self.evaluator,
            escalation_engine=self.escalation_engine
        )
        self.bridge = TelemetryIncidentLifecycleBridge(
            connector=self.connector,
            workspace_dir=self.workspace_dir
        )

    def test_end_to_end_lifecycle_bridge_integration(self):
        unique_metric_id = f"metric-{uuid.uuid4()}"
        random_anomaly_score = round(random.uniform(0.85, 0.99), 4)
        random_threshold = round(random.uniform(0.5, 0.8), 4)

        telemetry_payload = {
            "source_id": unique_metric_id,
            "anomaly_score": random_anomaly_score,
            "threshold": random_threshold,
            "status": "CRITICAL",
            "metadata": {
                "node": f"node-{uuid.uuid4().hex[:6]}",
                "cluster": "production-eu"
            }
        }

        result = self.bridge.process_lifecycle_event(telemetry_payload)

        self.assertIsInstance(result, dict)
        self.assertIn("incident_id", result)
        self.assertIn("lifecycle_status", result)
        self.assertEqual(result["lifecycle_status"], "CLOSED_VIA_ESCALATION")

        expected_file_pattern = f"incident_{unique_metric_id}"
        files_in_workspace = os.listdir(self.workspace_dir)
        matching_files = [f for f in files_in_workspace if unique_metric_id in f]
        
        self.assertTrue(
            len(matching_files) > 0,
            f"Ожидалось появление артефакта инцидента в рабочем каталоге {self.workspace_dir} для метрики {unique_metric_id}"
        )


if __name__ == "__main__":
    unittest.main()