import unittest
import uuid
import random
import os
import tempfile
from skills.incident_forensic_logger import IncidentForensicLogger
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector
from skills.incident_aggregator import IncidentAggregator

class TestIncidentForensicLoggerIntegration(unittest.TestCase):
    def setUp(self):
        self.telemetry_collector = SystemHealthTelemetryCollector()
        self.incident_aggregator = IncidentAggregator()
        self.forensic_logger = IncidentForensicLogger()
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_incident_forensic_logger_integration(self):
        random_incident_id = str(uuid.uuid4())
        random_metric_value = random.randint(1000, 99999)
        random_telemetry_source = f"source-{uuid.uuid4()}"

        telemetry_data = self.telemetry_collector.collect(
            source=random_telemetry_source,
            metric_value=random_metric_value
        )

        incident_data = self.incident_aggregator.aggregate(
            incident_id=random_incident_id,
            telemetry=telemetry_data
        )

        log_file_path = os.path.join(self.temp_dir.name, f"forensic_{random_incident_id}.log")
        
        result_status = self.forensic_logger.log_incident_traces(
            incident=incident_data,
            output_path=log_file_path
        )

        self.assertTrue(result_status, "Forensic logger must return success status.")
        self.assertTrue(os.path.exists(log_file_path), "Forensic log file must be physically created.")

        with open(log_file_path, 'r', encoding='utf-8') as f:
            log_content = f.read()

        self.assertIn(random_incident_id, log_content, "Log must contain the exact random incident ID.")
        self.assertIn(str(random_metric_value), log_content, "Log must contain the correlated telemetry metric value.")
        self.assertIn(random_telemetry_source, log_content, "Log must contain the telemetry source identifier.")

if __name__ == '__main__':
    unittest.main()