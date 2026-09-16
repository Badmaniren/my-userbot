import unittest
import uuid
import random
import os
from datetime import datetime

from skills.incident_sla_tracker import incident_sla_tracker
from skills.incident_sla_mitigation_planner import incident_sla_mitigation_planner
from skills.incident_sla_post_mortem_reporter import (
    IncidentSLAPostMortemReporter,
    incident_sla_post_mortem_reporter
)

class TestIncidentSLAPostMortemReporterIntegration(unittest.TestCase):

    def test_end_to_end_post_mortem_workflow(self):
        incident_id = f"inc-{uuid.uuid4()}"
        breach_reason = f"Network timeout breach {random.randint(100, 999)}"
        downtime_minutes = random.randint(15, 120)
        recommended_mitigation = f"Upgrade network bandwidth patch {random.randint(10, 99)}"

        tracker_input = {
            "incident_id": incident_id,
            "downtime_minutes": downtime_minutes,
            "breach_reason": breach_reason,
            "status": "breached"
        }
        tracked_data = incident_sla_tracker(tracker_input)

        planner_input = {
            "incident_id": incident_id,
            "recommended_mitigation": recommended_mitigation,
            "severity": "HIGH"
        }
        planned_data = incident_sla_mitigation_planner(planner_input)

        reporter = IncidentSLAPostMortemReporter(
            incident_sla_tracker=incident_sla_tracker,
            incident_sla_mitigation_planner=incident_sla_mitigation_planner
        )

        report = reporter.generate_report(incident_id)

        self.assertEqual(report["incident_id"], incident_id)
        self.assertEqual(report["downtime_minutes"], downtime_minutes)
        self.assertEqual(report["breach_reason"], breach_reason)
        self.assertEqual(report["mitigation_action"], recommended_mitigation)
        self.assertEqual(report["status"], "breached")
        self.assertIn("generated_at", report)

        temp_filepath = f"test_report_{uuid.uuid4()}.json"
        try:
            exported_path = reporter.export_report(incident_id, temp_filepath)
            self.assertTrue(os.path.exists(exported_path))

            with open(exported_path, "r", encoding="utf-8") as f:
                file_content = f.read()
                self.assertIn(incident_id, file_content)
                self.assertIn(breach_reason, file_content)
        finally:
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)

        batch_summary = reporter.generate_batch_summary([incident_id, f"fake-inc-{uuid.uuid4()}"])
        self.assertEqual(batch_summary["total_analyzed"], 1)
        self.assertEqual(len(batch_summary["reports"]), 1)
        self.assertEqual(batch_summary["reports"][0]["incident_id"], incident_id)

        functional_payload = {
            "incident_id": incident_id,
            "tracker_data": {
                "downtime_minutes": downtime_minutes,
                "status": "resolved"
            },
            "mitigation_data": {
                "recommended_mitigation": recommended_mitigation
            }
        }
        functional_result = incident_sla_post_mortem_reporter(functional_payload)
        self.assertIn("rep-", functional_result["report_id"])
        self.assertEqual(functional_result["incident_id"], incident_id)
        self.assertEqual(functional_result["breach_duration_minutes"], downtime_minutes)
        self.assertEqual(functional_result["mitigation_action"], recommended_mitigation)
        self.assertEqual(functional_result["status"], "resolved")

if __name__ == "__main__":
    unittest.main()