import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import json
import io
from datetime import datetime

from skills.repo_incident_tracker import IncidentTracker, IncidentStatus, IncidentSeverity

class TestRepoIncidentTracker(unittest.TestCase):
    def setUp(self):
        self.test_filepath = f"incidents_{uuid.uuid4().hex}.json"
        self.tracker = IncidentTracker(storage_path=self.test_filepath)

    def test_enums_exist_and_correct(self):
        self.assertEqual(IncidentStatus.OPEN.value, "open")
        self.assertEqual(IncidentStatus.IN_PROGRESS.value, "in_progress")
        self.assertEqual(IncidentStatus.RESOLVED.value, "resolved")
        self.assertEqual(IncidentStatus.CLOSED.value, "closed")

        self.assertEqual(IncidentSeverity.LOW.value, "low")
        self.assertEqual(IncidentSeverity.MEDIUM.value, "medium")
        self.assertEqual(IncidentSeverity.HIGH.value, "high")
        self.assertEqual(IncidentSeverity.CRITICAL.value, "critical")

    def test_create_incident(self):
        title = f"anomaly_{uuid.uuid4().hex}"
        description = f"desc_{uuid.uuid4().hex}"
        severity = random.choice(list(IncidentSeverity))

        with patch("builtins.open", mock_open()) as mock_file, \
             patch("os.path.exists", return_value=False):

            incident_id = self.tracker.create_incident(
                title=title,
                description=description,
                severity=severity
            )

            self.assertIsNotNone(incident_id)
            incident = self.tracker.get_incident(incident_id)
            self.assertEqual(incident["title"], title)
            self.assertEqual(incident["description"], description)
            self.assertEqual(incident["severity"], severity.value if isinstance(severity, IncidentSeverity) else severity)
            self.assertEqual(incident["status"], IncidentStatus.OPEN.value)

    def test_update_incident_status(self):
        title = f"anomaly_{uuid.uuid4().hex}"
        description = f"desc_{uuid.uuid4().hex}"
        severity = random.choice(list(IncidentSeverity))

        with patch("builtins.open", mock_open()) as mock_file, \
             patch("os.path.exists", return_value=False):

            incident_id = self.tracker.create_incident(
                title=title,
                description=description,
                severity=severity
            )

            new_status = random.choice([IncidentStatus.IN_PROGRESS, IncidentStatus.RESOLVED, IncidentStatus.CLOSED])
            self.tracker.update_status(incident_id, new_status)

            updated = self.tracker.get_incident(incident_id)
            self.assertEqual(updated["status"], new_status.value if isinstance(new_status, IncidentStatus) else new_status)

    def test_list_incidents_filtering(self):
        with patch("builtins.open", mock_open()) as mock_file, \
             patch("os.path.exists", return_value=False):

            id1 = self.tracker.create_incident("Inc 1", "Desc 1", IncidentSeverity.LOW)
            id2 = self.tracker.create_incident("Inc 2", "Desc 2", IncidentSeverity.HIGH)

            self.tracker.update_status(id2, IncidentStatus.RESOLVED)

            all_incidents = self.tracker.list_incidents()
            self.assertEqual(len(all_incidents), 2)

            open_incidents = self.tracker.list_incidents(status=IncidentStatus.OPEN)
            self.assertEqual(len(open_incidents), 1)
            self.assertEqual(open_incidents[0]["id"], id1)

            high_incidents = self.tracker.list_incidents(severity=IncidentSeverity.HIGH)
            self.assertEqual(len(high_incidents), 1)
            self.assertEqual(high_incidents[0]["id"], id2)

    def test_persistence_load_save(self):
        random_title = f"persisted_{uuid.uuid4().hex}"
        mock_data = json.dumps({
            "incidents": {
                "test-id-123": {
                    "id": "test-id-123",
                    "title": random_title,
                    "description": "some desc",
                    "severity": "critical",
                    "status": "open",
                    "created_at": datetime.now().isoformat()
                }
            }
        })

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_data)):

            new_tracker = IncidentTracker(storage_path=self.test_filepath)
            incident = new_tracker.get_incident("test-id-123")
            self.assertIsNotNone(incident)
            self.assertEqual(incident["title"], random_title)
            self.assertEqual(incident["severity"], "critical")

    def test_nonexistent_incident_handling(self):
        fake_id = uuid.uuid4().hex
        with patch("os.path.exists", return_value=False):
            incident = self.tracker.get_incident(fake_id)
            self.assertIsNone(incident)

            with self.assertRaises(Exception):
                self.tracker.update_status(fake_id, IncidentStatus.CLOSED)