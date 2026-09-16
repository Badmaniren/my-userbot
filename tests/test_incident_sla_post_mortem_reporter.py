import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import json
from datetime import datetime

from skills.incident_sla_post_mortem_reporter import (
    IncidentSLAPostMortemReporter,
    incident_sla_post_mortem_reporter
)


class TestIncidentSLAPostMortemReporter(unittest.TestCase):

    def setUp(self):
        self.mock_tracker = MagicMock()
        self.mock_planner = MagicMock()
        self.reporter = IncidentSLAPostMortemReporter(self.mock_tracker, self.mock_planner)
        self.random_incident_id = f"inc-{uuid.uuid4().hex[:8]}"

    def test_generate_report_success(self):
        breach_reason_val = f"reason-{uuid.uuid4().hex[:6]}"
        mitigation_val = f"action-{uuid.uuid4().hex[:6]}"
        downtime_val = random.randint(10, 500)
        status_val = random.choice(["breached", "critical", "investigating"])

        self.mock_tracker.get_breach_details.return_value = {
            "incident_id": self.random_incident_id,
            "breach_reason": breach_reason_val,
            "downtime_minutes": downtime_val,
            "status": status_val
        }
        self.mock_planner.get_mitigation_plan.return_value = {
            "incident_id": self.random_incident_id,
            "recommended_mitigation": mitigation_val
        }

        report = self.reporter.generate_report(self.random_incident_id)

        self.assertEqual(report["incident_id"], self.random_incident_id)
        self.assertEqual(report["breach_reason"], breach_reason_val)
        self.assertEqual(report["mitigation_action"], mitigation_val)
        self.assertEqual(report["downtime_minutes"], downtime_val)
        self.assertEqual(report["status"], status_val)
        self.assertIn("generated_at", report)

    def test_generate_report_not_found_raises_value_error(self):
        self.mock_tracker.get_breach_details.return_value = None
        self.mock_planner.get_mitigation_plan.return_value = None

        with self.assertRaises(ValueError):
            self.reporter.generate_report(self.random_incident_id)

    def test_generate_report_partial_data_tracker_only(self):
        breach_reason_val = f"reason-{uuid.uuid4().hex[:6]}"
        downtime_val = random.randint(1, 100)

        self.mock_tracker.get_breach_details.return_value = {
            "incident_id": self.random_incident_id,
            "breach_reason": breach_reason_val,
            "downtime_minutes": downtime_val,
            "status": "open"
        }
        self.mock_planner.get_mitigation_plan.return_value = None

        report = self.reporter.generate_report(self.random_incident_id)

        self.assertEqual(report["incident_id"], self.random_incident_id)
        self.assertEqual(report["breach_reason"], breach_reason_val)
        self.assertIsNone(report["mitigation_action"])
        self.assertEqual(report["downtime_minutes"], downtime_val)

    def test_generate_report_partial_data_planner_only(self):
        mitigation_val = f"action-{uuid.uuid4().hex[:6]}"

        self.mock_tracker.get_breach_details.return_value = None
        self.mock_planner.get_mitigation_plan.return_value = {
            "incident_id": self.random_incident_id,
            "recommended_mitigation": mitigation_val
        }

        report = self.reporter.generate_report(self.random_incident_id)

        self.assertEqual(report["incident_id"], self.random_incident_id)
        self.assertIsNone(report["breach_reason"])
        self.assertEqual(report["mitigation_action"], mitigation_val)
        self.assertIsNone(report["downtime_minutes"])

    def test_export_report_writes_file(self):
        filepath = f"/tmp/{uuid.uuid4().hex}.json"
        breach_reason_val = f"reason-{uuid.uuid4().hex[:6]}"

        self.mock_tracker.get_breach_details.return_value = {
            "incident_id": self.random_incident_id,
            "breach_reason": breach_reason_val,
            "downtime_minutes": random.randint(5, 50),
            "status": "closed"
        }
        self.mock_planner.get_mitigation_plan.return_value = None

        mock_file = MagicMock()
        with patch("builtins.open", return_value=mock_file) as mock_open:
            returned_path = self.reporter.export_report(self.random_incident_id, filepath)
            mock_open.assert_called_once_with(filepath, "w", encoding="utf-8")
            self.assertEqual(returned_path, filepath)
            mock_file.__enter__().write.assert_called()

    def test_generate_batch_summary(self):
        inc_id_1 = f"inc-{uuid.uuid4().hex[:6]}"
        inc_id_2 = f"inc-{uuid.uuid4().hex[:6]}"

        def side_effect(inc_id):
            if inc_id == inc_id_1:
                return {"incident_id": inc_id_1, "breach_reason": "r1"}
            elif inc_id == inc_id_2:
                return {"incident_id": inc_id_2, "breach_reason": "r2"}
            return None

        self.mock_tracker.get_breach_details.side_effect = side_effect
        self.mock_planner.get_mitigation_plan.return_value = None

        batch = self.reporter.generate_batch_summary([inc_id_1, inc_id_2, f"inc-{uuid.uuid4().hex[:6]}"])

        self.assertEqual(batch["total_analyzed"], 2)
        self.assertEqual(len(batch["reports"]), 2)
        self.assertIn("generated_at", batch)

    def test_functional_helper_incident_sla_post_mortem_reporter(self):
        inc_id = f"inc-{uuid.uuid4().hex[:8]}"
        duration = random.randint(10, 1000)
        action = f"action-{uuid.uuid4().hex[:6]}"
        status = f"status-{uuid.uuid4().hex[:4]}"

        data = {
            "incident_id": inc_id,
            "tracker_data": {
                "breach_duration": duration,
                "status": status
            },
            "mitigation_data": {
                "mitigation_action": action
            }
        }

        result = incident_sla_post_mortem_reporter(data)

        self.assertEqual(result["incident_id"], inc_id)
        self.assertEqual(result["breach_duration_minutes"], duration)
        self.assertEqual(result["mitigation_action"], action)
        self.assertEqual(result["status"], status)
        self.assertTrue(result["report_id"].startswith("rep-"))
        self.assertIn("generated_at", result)

    def test_functional_helper_fallback_fields(self):
        inc_id = f"inc-{uuid.uuid4().hex[:8]}"
        downtime = random.randint(5, 500)
        recommended_action = f"rec-{uuid.uuid4().hex[:6]}"

        data = {
            "incident_id": inc_id,
            "tracker_data": {
                "downtime_minutes": downtime
            },
            "mitigation_data": {
                "recommended_mitigation": recommended_action
            }
        }

        result = incident_sla_post_mortem_reporter(data)

        self.assertEqual(result["incident_id"], inc_id)
        self.assertEqual(result["breach_duration_minutes"], downtime)
        self.assertEqual(result["mitigation_action"], recommended_action)
        self.assertEqual(result["status"], "processed")
        self.assertTrue(result["report_id"].startswith("rep-"))


if __name__ == "__main__":
    unittest.main()