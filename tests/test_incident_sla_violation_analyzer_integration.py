import unittest
import uuid
import random
import os
from skills.incident_sla_violation_analyzer import (
    incident_sla_violation_analyzer,
    incident_sla_tracker,
    incident_severity_evaluator,
    incident_business_loss_reporter
)

class TestIncidentSLAViolationAnalyzerIntegration(unittest.TestCase):
    def test_sla_violation_analyzer_pipeline(self):
        random_incident_id = str(uuid.uuid4())
        random_sla_limit_hours = random.randint(1, 72)
        random_downtime_minutes = random.randint(30, 1440)

        tracker_result = incident_sla_tracker(
            incident_id=random_incident_id,
            sla_limit=random_sla_limit_hours
        )
        self.assertIsNotNone(tracker_result)

        severity_result = incident_severity_evaluator(
            incident_id=random_incident_id,
            downtime=random_downtime_minutes
        )
        self.assertIsNotNone(severity_result)

        loss_report = incident_business_loss_reporter(
            incident_id=random_incident_id,
            impact_factor=random.random() * 100.0
        )
        self.assertIsNotNone(loss_report)

        analysis_output = incident_sla_violation_analyzer(
            incident_id=random_incident_id,
            sla_limit_hours=random_sla_limit_hours,
            downtime_minutes=random_downtime_minutes
        )

        self.assertIsInstance(analysis_output, dict)
        self.assertIn("incident_id", analysis_output)
        self.assertEqual(analysis_output["incident_id"], random_incident_id)
        self.assertTrue(analysis_output.get("violation_detected", False))

        if "report_path" in analysis_output:
            self.assertTrue(os.path.exists(analysis_output["report_path"]))
            os.remove(analysis_output["report_path"])

if __name__ == "__main__":
    unittest.main()