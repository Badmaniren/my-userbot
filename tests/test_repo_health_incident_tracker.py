import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
from skills.repo_health_incident_tracker import RepoHealthIncidentTracker


class TestRepoHealthIncidentTracker(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo_{uuid.uuid4().hex[:8]}"
        self.tracker = RepoHealthIncidentTracker(repo_path=self.repo_path)

    def test_init_state(self):
        self.assertEqual(self.tracker.repo_path, self.repo_path)
        self.assertEqual(self.tracker._incidents, {})

    @patch('skills.repo_health_incident_tracker.repo_logger')
    def test_log_incident_with_repo_logger_object(self, mock_repo_logger):
        incident_id = uuid.uuid4().hex[:6]
        severity = random.choice(["INFO", "WARNING", "ERROR", "CRITICAL"])
        message = f"Msg_{uuid.uuid4().hex[:8]}"

        mock_logger_instance = MagicMock()
        mock_repo_logger.RepoLogger.return_value = mock_logger_instance

        del mock_repo_logger.repo_logger
        if hasattr(mock_repo_logger, 'log'):
            del mock_repo_logger.log

        self.tracker.log_incident(incident_id, severity, message)

        expected_log = f"Incident {incident_id} [{severity}]: {message}"
        mock_logger_instance.log.assert_called_once_with(expected_log)

    @patch('skills.repo_health_incident_tracker.repo_logger')
    def test_log_incident_with_repo_logger_event(self, mock_repo_logger):
        incident_id = uuid.uuid4().hex[:6]
        severity = random.choice(["INFO", "WARNING", "ERROR", "CRITICAL"])
        message = f"Msg_{uuid.uuid4().hex[:8]}"

        mock_logger_instance = MagicMock()
        del mock_logger_instance.log
        mock_repo_logger.RepoLogger.return_value = mock_logger_instance

        if hasattr(mock_repo_logger, 'repo_logger'):
            del mock_repo_logger.repo_logger
        if hasattr(mock_repo_logger, 'log'):
            del mock_repo_logger.log

        self.tracker.log_incident(incident_id, severity, message)

        mock_logger_instance.log_event.assert_called_once_with(level=severity, message=message)

    @patch('skills.repo_health_incident_tracker.repo_logger')
    def test_log_incident_integrity(self, mock_repo_logger):
        incident_id = uuid.uuid4().hex[:6]
        severity = random.choice(["INFO", "WARNING", "ERROR", "CRITICAL"])
        message = f"Msg_{uuid.uuid4().hex[:8]}"

        mock_logger = MagicMock()
        mock_repo_logger.repo_logger = mock_logger

        self.tracker.log_incident(incident_id, severity, message)

        expected_log = f"Incident {incident_id} [{severity}]: {message}"
        mock_logger.log.assert_called_once_with(expected_log)

    @patch('skills.repo_health_incident_tracker.repo_health_anomaly_remediation_pipeline')
    def test_trigger_remediation(self, mock_pipeline):
        anomaly_id = f"anom_{uuid.uuid4().hex[:6]}"
        target_repo = f"https://github.com/org_{uuid.uuid4().hex[:4]}/repo_{uuid.uuid4().hex[:4]}"
        expected_result = {"status": "remediated", "id": anomaly_id}
        mock_pipeline.execute.return_value = expected_result

        result = self.tracker.trigger_remediation(anomaly_id, target_repo)

        mock_pipeline.execute.assert_called_once_with(anomaly_id=anomaly_id, repo_url=target_repo)
        self.assertEqual(result, expected_result)

    @patch('skills.repo_health_incident_tracker.repo_health_diagnostic')
    def test_process_incident_stream(self, mock_diagnostic):
        stream_data = f"stream_payload_{uuid.uuid4().hex}".encode('utf-8')
        stream = io.BytesIO(stream_data)
        expected_parsed = {"diagnostic": "ok", "hash": uuid.uuid4().hex[:6]}
        mock_diagnostic.parse_stream.return_value = expected_parsed

        result = self.tracker.process_incident_stream(stream)

        mock_diagnostic.parse_stream.assert_called_once_with(stream_data)
        self.assertEqual(result, expected_parsed)

    @patch('skills.repo_health_incident_tracker.repo_health_anomaly_inspector')
    def test_check_anomaly_status(self, mock_inspector):
        incident_code = f"INC-{random.randint(1000, 9999)}"
        expected_inspection = {"code": incident_code, "severity": "HIGH"}
        mock_inspector.inspect.return_value = expected_inspection

        result = self.tracker.check_anomaly_status(incident_code)

        mock_inspector.inspect.assert_called_once_with(incident_code)
        self.assertEqual(result, expected_inspection)

    @patch('skills.repo_health_incident_tracker.repo_health_dispatcher')
    def test_dispatch_incident(self, mock_dispatcher):
        incident_type = f"type_{uuid.uuid4().hex[:5]}"
        payload = {"data": uuid.uuid4().hex}

        self.tracker.dispatch_incident(incident_type, payload)

        mock_dispatcher.route.assert_called_once_with(incident_type, payload)

    @patch('skills.repo_health_incident_tracker.repo_health_guardian')
    def test_verify_repo_health(self, mock_guardian):
        repo_p = f"/path/to/{uuid.uuid4().hex[:6]}"
        token = f"tok_{uuid.uuid4().hex[:10]}"
        expected_validation = {"valid": True, "score": random.random()}
        mock_guardian.validate_health.return_value = expected_validation

        result = self.tracker.verify_repo_health(repo_p, token)

        mock_guardian.validate_health.assert_called_once_with(repo_p, token)
        self.assertEqual(result, expected_validation)

    def test_register_incident(self):
        incident_id = f"inc_{uuid.uuid4().hex[:6]}"
        details = {"error": f"err_{uuid.uuid4().hex[:4]}"}

        registered = self.tracker.register_incident(incident_id, details)

        self.assertEqual(registered["incident_id"], incident_id)
        self.assertEqual(registered["details"], details)
        self.assertEqual(registered["status"], "RESOLVED")
        self.assertIn(incident_id, self.tracker._incidents)
        self.assertEqual(self.tracker._incidents[incident_id]["status"], "RESOLVED")

    def test_get_incident_existing(self):
        incident_id = f"inc_{uuid.uuid4().hex[:6]}"
        details = {"info": uuid.uuid4().hex[:8]}
        self.tracker.register_incident(incident_id, details)

        inc = self.tracker.get_incident(incident_id)
        self.assertEqual(inc["incident_id"], incident_id)
        self.assertEqual(inc["status"], "RESOLVED")
        self.assertEqual(inc["details"], details)

    def test_get_incident_missing(self):
        incident_id = f"inc_missing_{uuid.uuid4().hex[:6]}"
        inc = self.tracker.get_incident(incident_id)
        self.assertEqual(inc["incident_id"], incident_id)
        self.assertEqual(inc["status"], "RESOLVED")
        self.assertNotIn("details", inc)