import unittest
import uuid
import random
import io
import time

from skills.incident_aggregator import IncidentAggregator
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.incident_post_mortem_generator import (
    IncidentPostMortemGenerator,
    PostMortemReport,
    IncompleteRecoveryDataError
)


class TestIncidentPostMortemGeneratorIntegration(unittest.TestCase):

    def setUp(self):
        self.incident_id = str(uuid.uuid4())
        self.service_name = f"service-{random.randint(100, 999)}"
        self.severity_level = random.choice(["SEV1", "SEV2", "SEV3"])
        self.root_cause = f"Root cause analysis id {random.randint(1000, 9999)}"
        self.component_name = f"component-{random.randint(1, 50)}"

        self.aggregator = IncidentAggregator()
        self.recovery_hub = ErrorRecoveryHub()

        self.generator = IncidentPostMortemGenerator(
            incident_aggregator=self.aggregator,
            error_recovery_hub=self.recovery_hub
        )

    def test_generate_post_mortem_full_integration(self):
        current_time = time.time()
        occurred = current_time - 3600
        detected = current_time - 1800
        resolved = current_time

        incident_data = {
            "incident_id": self.incident_id,
            "service": self.service_name,
            "severity": self.severity_level,
            "root_cause_summary": self.root_cause,
            "affected_components": [self.component_name],
            "occurred_at": occurred,
            "detected_at": detected,
            "resolved_at": resolved,
            "title": "Random network failure"
        }

        self.aggregator.storage = {
            self.incident_id: incident_data
        }

        recovery_action_name = f"action-{random.randint(100, 999)}"
        recovery_log = {
            "timestamp": detected + 300,
            "action": recovery_action_name,
            "details": "Restarted pod successfully"
        }

        self.recovery_hub.logs_storage = {
            self.incident_id: [recovery_log]
        }

        report = self.generator.generate_post_mortem(self.incident_id, allow_partial=False)

        self.assertIsInstance(report, PostMortemReport)
        self.assertEqual(report.incident_id, self.incident_id)
        self.assertEqual(report.service, self.service_name)
        self.assertEqual(report.severity, self.severity_level)
        self.assertEqual(report.root_cause, self.root_cause)

        self.assertIn(self.component_name, report.affected_components)

        timeline = report.get("timeline", [])
        self.assertGreaterEqual(len(timeline), 3)

        actions_found = [t for t in timeline if t["event"] == recovery_action_name]
        self.assertEqual(len(actions_found), 1)

        stream = io.StringIO()
        self.generator.export_report(report, stream, format_type="markdown")
        exported_content = stream.getvalue()

        self.assertIn(self.incident_id, exported_content)
        self.assertIn(self.service_name, exported_content)
        self.assertIn(self.severity_level, exported_content)
        self.assertIn(self.root_cause, exported_content)

    def test_missing_recovery_logs_raises_error(self):
        incident_data = {
            "incident_id": self.incident_id,
            "service": self.service_name,
            "severity": self.severity_level,
            "root_cause_summary": self.root_cause,
            "affected_components": [self.component_name]
        }

        self.aggregator.storage = {
            self.incident_id: incident_data
        }

        self.recovery_hub.logs_storage = {}

        with self.assertRaises(IncompleteRecoveryDataError):
            self.generator.generate_post_mortem(self.incident_id, allow_partial=False)


if __name__ == "__main__":
    unittest.main()