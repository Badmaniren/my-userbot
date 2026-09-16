import unittest
from unittest.mock import patch, MagicMock
import time
import uuid
import random
import io

from skills.incident_sla_sla_tracker import (
    SlaState,
    SlaViolationException,
    IncidentSlaTracker,
    incident_sla_sla_tracker
)

class TestIncidentSlaTracker(unittest.TestCase):
    def setUp(self):
        self.incident_aggregator_mock = MagicMock()
        self.impact_analyzer_mock = MagicMock()
        self.tracker = IncidentSlaTracker(
            self.incident_aggregator_mock,
            self.impact_analyzer_mock
        )

    def test_initialize_incident_sla(self):
        inc_id = f"INC-{uuid.uuid4().hex[:8]}"
        limit = random.randint(30, 300)

        details_data = {"id": inc_id, "status": "OPEN"}
        self.incident_aggregator_mock.get_incident_details.return_value = details_data
        self.impact_analyzer_mock.calculate_urgency.return_value = limit

        result = self.tracker.initialize_incident_sla(inc_id)

        self.incident_aggregator_mock.get_incident_details.assert_called_once_with(inc_id)
        self.impact_analyzer_mock.calculate_urgency.assert_called_once_with(details_data)

        self.assertEqual(result["incident_id"], inc_id)
        self.assertEqual(result["state"], SlaState.TRACKING.value)
        self.assertEqual(result["limit_seconds"], limit)
        self.assertIn(inc_id, self.tracker.active_slas)

    def test_check_violation_not_found(self):
        inc_id = f"INC-{uuid.uuid4().hex[:8]}"
        with self.assertRaises(KeyError):
            self.tracker.check_violation(inc_id)

    def test_check_violation_not_violated(self):
        inc_id = f"INC-{uuid.uuid4().hex[:8]}"
        self.tracker.active_slas[inc_id] = {
            "start_time": time.time(),
            "limit_seconds": 1000,
            "state": SlaState.TRACKING.value
        }

        is_violated = self.tracker.check_violation(inc_id)
        self.assertFalse(is_violated)
        self.assertEqual(self.tracker.active_slas[inc_id]["state"], SlaState.TRACKING.value)

    def test_check_violation_triggered(self):
        inc_id = f"INC-{uuid.uuid4().hex[:8]}"
        self.tracker.active_slas[inc_id] = {
            "start_time": time.time() - 500,
            "limit_seconds": 100,
            "state": SlaState.TRACKING.value
        }

        is_violated = self.tracker.check_violation(inc_id)
        self.assertTrue(is_violated)
        self.assertEqual(self.tracker.active_slas[inc_id]["state"], SlaState.VIOLATED.value)

    def test_resolve_incident_not_found(self):
        inc_id = f"INC-{uuid.uuid4().hex[:8]}"
        code = f"RES-{random.randint(100,999)}"
        with self.assertRaises(KeyError):
            self.tracker.resolve_incident(inc_id, code)

    def test_resolve_incident_success(self):
        inc_id = f"INC-{uuid.uuid4().hex[:8]}"
        code = f"RES-{random.randint(100,999)}"
        self.tracker.active_slas[inc_id] = {
            "start_time": time.time(),
            "limit_seconds": 300,
            "state": SlaState.TRACKING.value
        }

        res = self.tracker.resolve_incident(inc_id, code)
        self.assertTrue(res["success"])
        self.assertEqual(res["resolution_code"], code)
        self.assertEqual(self.tracker.active_slas[inc_id]["state"], SlaState.RESOLVED.value)

    def test_generate_sla_report(self):
        key1 = f"metric_{uuid.uuid4().hex[:4]}"
        val1 = f"val_{uuid.uuid4().hex[:4]}"
        key2 = f"metric_{uuid.uuid4().hex[:4]}"
        val2 = f"val_{uuid.uuid4().hex[:4]}"

        raw_stream_data = f"{key1}:{val1}\n{key2}:{val2}\n".encode('utf-8')
        stream_mock = io.BytesIO(raw_stream_data)

        self.impact_analyzer_mock.export_metrics_stream.return_value = stream_mock

        report = self.tracker.generate_sla_report()
        self.assertEqual(report.get(key1), val1)
        self.assertEqual(report.get(key2), val2)

    def test_functional_incident_sla_sla_tracker(self):
        inc_id = f"INC-{uuid.uuid4().hex[:8]}"
        budget = random.randint(10, 120)
        payload = {
            "incident_id": inc_id,
            "time_budget_minutes": budget
        }

        res = incident_sla_sla_tracker(payload)
        self.assertEqual(res["incident_id"], inc_id)
        self.assertEqual(res["sla_status"], SlaState.TRACKING.value)
        self.assertGreater(res["deadline_timestamp"], time.time())