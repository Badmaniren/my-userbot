import unittest
import os
import uuid
import random
from skills.audit_exporter_hub import AuditExporterHub, export_and_audit_reports, process_audit_stream
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger

class TestAuditExporterHubIntegration(unittest.TestCase):
    def setUp(self):
        self.unique_id = str(uuid.uuid4())[:8]
        self.log_file = f"test_audit_log_{self.unique_id}.json"
        self.repo_path = f"./test_repo_{self.unique_id}"

        os.makedirs(self.repo_path, exist_ok=True)

        self.source = f"source_{self.unique_id}"
        self.severity = round(random.uniform(0.1, 1.0), 2)
        self.details = f"Integration test anomaly details {uuid.uuid4()}"
        self.telemetry = {"cpu_load": random.randint(10, 99), "memory": random.randint(100, 999)}

    def tearDown(self):
        if os.path.exists(self.log_file):
            try:
                os.remove(self.log_file)
            except OSError:
                pass
        if os.path.exists(self.repo_path):
            try:
                os.rmdir(self.repo_path)
            except OSError:
                pass

    def test_integration_exporter_hub_and_logger(self):
        audit_hub = AnomalyAuditHub(repo_path=self.repo_path, log_path=self.log_file, threshold=self.severity)
        logger = AnomalyLogger(log_path=self.log_file)

        logger.log_anomaly(
            source=self.source,
            severity=self.severity,
            details=self.details,
            telemetry_snapshot=self.telemetry
        )

        hub = AuditExporterHub(audit_hub=audit_hub, logger=logger)
        report = hub.export_reports()

        self.assertIsInstance(report, dict)

        structured_logs = logger.get_structured_report()
        self.assertIsNotNone(structured_logs)

        anomalies = logger.get_anomalies()
        self.assertTrue(any(a.get("source") == self.source for a in anomalies))

    def test_integration_functional_wrapper(self):
        result = export_and_audit_reports(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.severity
        )
        self.assertIsInstance(result, dict)

    def test_integration_process_audit_stream(self):
        setattr(process_audit_stream, '_log_path', self.log_file)

        success = process_audit_stream(
            source=self.source,
            severity=self.severity,
            details=self.details,
            telemetry_data=self.telemetry
        )

        self.assertTrue(success)

        logger = AnomalyLogger(log_path=self.log_file)
        anomalies = logger.get_anomalies()

        found = False
        for anomaly in anomalies:
            if anomaly.get("details") == self.details:
                found = True
                break

        self.assertTrue(found, "Logged anomaly with random details should be found via AnomalyLogger.")

if __name__ == "__main__":
    unittest.main()