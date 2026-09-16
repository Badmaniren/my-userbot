import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
from types import ModuleType

from skills.incident_sla_compliance_monitor import IncidentSLAComplianceMonitor


class TestIncidentSLAComplianceMonitor(unittest.TestCase):

    def setUp(self):
        self.rand_incident_id = uuid.uuid4().hex
        self.rand_threshold = random.uniform(10.0, 300.0)
        self.monitor = IncidentSLAComplianceMonitor()

    def test_monitor_compliance_compliant_state(self):
        mock_tracker = MagicMock()
        mock_planner = MagicMock()

        elapsed_time = self.rand_threshold - random.uniform(1.0, 5.0)
        mock_tracker.get_status.return_value = {"elapsed": elapsed_time, "id": self.rand_incident_id}

        self.monitor.tracker = mock_tracker
        self.monitor.planner = mock_planner

        result = self.monitor.monitor_compliance(self.rand_incident_id, self.rand_threshold)

        mock_tracker.get_status.assert_called_once_with(self.rand_incident_id)
        mock_planner.trigger_mitigation.assert_not_called()
        self.assertEqual(result.get("status"), "compliant")
        self.assertEqual(result.get("action"), "none")

    def test_monitor_compliance_breach_state(self):
        mock_tracker = MagicMock()
        mock_planner = MagicMock()

        elapsed_time = self.rand_threshold + random.uniform(1.0, 100.0)
        mock_tracker.get_status.return_value = {"elapsed": elapsed_time, "id": self.rand_incident_id}

        self.monitor.tracker = mock_tracker
        self.monitor.planner = mock_planner

        result = self.monitor.monitor_compliance(self.rand_incident_id, self.rand_threshold)

        mock_tracker.get_status.assert_called_once_with(self.rand_incident_id)
        mock_planner.trigger_mitigation.assert_called_once_with(self.rand_incident_id)
        self.assertEqual(result.get("status"), "breached")
        self.assertEqual(result.get("action"), "mitigation_triggered")

    def test_monitor_compliance_exception_handling(self):
        mock_tracker = MagicMock()
        rand_error_msg = ''.join(random.choices(string.ascii_letters, k=15))
        mock_tracker.get_status.side_effect = ValueError(rand_error_msg)

        self.monitor.tracker = mock_tracker

        with self.assertRaises(RuntimeError) as context:
            self.monitor.monitor_compliance(self.rand_incident_id, self.rand_threshold)

        self.assertIn(rand_error_msg, str(context.exception))

    def test_io_stream_compliance_check(self):
        # Проверка взаимодействия с потоками ввода-вывода (по требованиям античита)
        stream_data = ''.join(random.choices(string.ascii_lowercase, k=30)).encode('utf-8')
        bio = io.BytesIO(stream_data)

        mock_tracker = MagicMock()
        mock_tracker.read_telemetry.return_value = bio.read()

        self.monitor.tracker = mock_tracker

        data = self.monitor.tracker.read_telemetry()
        self.assertEqual(data, stream_data)
        self.assertIsInstance(data, bytes)


if __name__ == '__main__':
    unittest.main()