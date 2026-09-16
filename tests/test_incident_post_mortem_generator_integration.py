import unittest
import uuid
import random
import os
import tempfile
import hashlib

from skills.incident_post_mortem_generator import (
    IncidentPostMortemGenerator,
    generate_incident_post_mortem
)
from skills.incident_aggregator import IncidentAggregator
from skills.incident_trend_analyzer import IncidentTrendAnalyzer
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.recovery_report_exporter import RecoveryReportExporter


class IntegrationTestIncidentPostMortemGenerator(unittest.TestCase):

    def setUp(self):
        self.incident_aggregator = IncidentAggregator()
        self.incident_trend_analyzer = IncidentTrendAnalyzer()
        self.error_recovery_hub = ErrorRecoveryHub()
        self.recovery_report_exporter = RecoveryReportExporter()

        self.generator = IncidentPostMortemGenerator(
            incident_aggregator=self.incident_aggregator,
            incident_trend_analyzer=self.incident_trend_analyzer,
            error_recovery_hub=self.error_recovery_hub,
            recovery_report_exporter=self.recovery_report_exporter
        )

    def test_end_to_end_post_mortem_generation_and_export(self):
        rand_suffix = uuid.uuid4().hex[:8]
        incident_id = f"INC-{rand_suffix}"
        error_code = f"ERR-{random.randint(1000, 9999)}"
        impact_score = random.randint(50, 100)

        log_fd, log_path = tempfile.mkstemp(suffix=".log")
        os.close(log_fd)
        telemetry_content = f"telemetry data for incident {incident_id} with error {error_code}".encode("utf-8")
        with open(log_path, "wb") as f:
            f.write(telemetry_content)

        expected_telemetry_hash = hashlib.sha256(telemetry_content).hexdigest()

        self.incident_aggregator.storage = getattr(self.incident_aggregator, "storage", {})
        self.incident_aggregator.storage[incident_id] = {
            "incident_id": incident_id,
            "error_code": error_code,
            "severity": "SEV-2",
            "impact_score": impact_score,
            "description": f"Integration test dynamic description {rand_suffix}",
            "log_pointer": log_path
        }

        self.error_recovery_hub.storage = getattr(self.error_recovery_hub, "storage", {})
        self.error_recovery_hub.storage[incident_id] = {
            "failed_attempts": random.randint(0, 3),
            "recovery_status": "FAILED"
        }

        report_payload = self.generator.generate(incident_id, include_raw_telemetry=True)

        self.assertEqual(report_payload["incident_id"], incident_id)
        self.assertEqual(report_payload["telemetry_hash"], expected_telemetry_hash)
        self.assertIn("export_path", report_payload)

        export_path = report_payload["export_path"]
        self.assertTrue(os.path.exists(export_path))

        with open(export_path, "r", encoding="utf-8") as f:
            exported_content = f.read()

        self.assertIn(incident_id, exported_content)
        self.assertIn(error_code, exported_content)

        out_dir = tempfile.mkdtemp()
        output_post_mortem_path = os.path.join(out_dir, f"{incident_id}_post_mortem.md")

        aggregated_data = self.incident_aggregator.get_incident(incident_id)
        trend_data = self.incident_trend_analyzer.analyze_trends(aggregated_data)
        recovery_history = self.error_recovery_hub.get_recovery_history(incident_id)

        result_path = generate_incident_post_mortem(
            incident_id=incident_id,
            aggregated_data=aggregated_data,
            trend_data=trend_data,
            recovery_history=recovery_history,
            output_path=output_post_mortem_path
        )

        self.assertEqual(result_path, output_post_mortem_path)
        self.assertTrue(os.path.exists(output_post_mortem_path))

        with open(output_post_mortem_path, "r", encoding="utf-8") as f:
            pm_content = f.read()

        self.assertIn(incident_id, pm_content)
        self.assertIn(error_code, pm_content)

        if os.path.exists(log_path):
            os.remove(log_path)
        if os.path.exists(export_path):
            os.remove(export_path)
        if os.path.exists(output_post_mortem_path):
            os.remove(output_post_mortem_path)
        if os.path.exists(out_dir):
            os.rmdir(out_dir)


if __name__ == "__main__":
    unittest.main()