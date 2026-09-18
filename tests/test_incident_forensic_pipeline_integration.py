import unittest
import uuid
import random
import os
from skills.incident_forensic_pipeline import incident_forensic_pipeline
from skills.system_health_telemetry_collector import system_health_telemetry_collector
from skills.system_health_audit_pipeline import system_health_audit_pipeline
from skills.incident_aggregator import incident_aggregator

class TestIncidentForensicPipelineIntegration(unittest.TestCase):
    def test_pipeline_execution_flow(self):
        unique_session_id = str(uuid.uuid4())
        random_metric_value = random.uniform(10.5, 99.9)
        test_artifact_path = f"forensic_report_{unique_session_id}.log"

        telemetry_data = system_health_telemetry_collector(
            session_id=unique_session_id,
            metric_threshold=random_metric_value
        )

        audit_data = system_health_audit_pipeline(
            telemetry_payload=telemetry_data
        )

        aggregated_incident = incident_aggregator(
            audit_report=audit_data,
            identifier=unique_session_id
        )

        pipeline_result = incident_forensic_pipeline(
            incident_input=aggregated_incident,
            output_file=test_artifact_path
        )

        self.assertIn(unique_session_id, pipeline_result)
        self.assertTrue(os.path.exists(test_artifact_path))

        with open(test_artifact_path, "r", encoding="utf-8") as file_handle:
            file_content = file_handle.read()
            self.assertIn(unique_session_id, file_content)

        if os.path.exists(test_artifact_path):
            os.remove(test_artifact_path)

if __name__ == "__main__":
    unittest.main()