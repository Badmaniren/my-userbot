import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import json
import io
import os

from skills.incident_compliance_report_generator import start_new, generate_compliance_report

class TestIncidentComplianceReportGenerator(unittest.TestCase):

    def test_start_new_incident_not_found(self):
        incident_id = uuid.uuid4().hex
        standard = uuid.uuid4().hex
        report_format = uuid.uuid4().hex

        with patch('skills.incident_aggregator.fetch_incident_data', return_value=None) as mock_fetch:
            with self.assertRaises(ValueError) as ctx:
                start_new(incident_id, standard, report_format, export_to_stream=False)
            
            self.assertIn(incident_id, str(ctx.exception))
            mock_fetch.assert_called_once_with(incident_id)

    def test_start_new_compliance_success_with_verify_compliance(self):
        incident_id = uuid.uuid4().hex
        standard = uuid.uuid4().hex
        report_format = uuid.uuid4().hex
        
        mock_incident_data = {"id": incident_id, "status": random.choice(["OPEN", "INVESTIGATING"])}
        mock_audit_tracks = [uuid.uuid4().hex, uuid.uuid4().hex]
        checked_items_val = random.randint(5, 20)
        mock_compliance_result = {
            "status": "APPROVED",
            "checked_items": checked_items_val
        }

        with patch('skills.incident_aggregator.fetch_incident_data', return_value=mock_incident_data) as mock_fetch, \
             patch('skills.incident_audit_trail_collector.collect_tracks', return_value=mock_audit_tracks) as mock_collect, \
             patch('skills.incident_forensics_compliance_checker') as mock_checker, \
             patch('skills.incident_auto_escalation_engine.trigger_escalation') as mock_escalation:
            
            delattr(mock_checker, "check_compliance")
            mock_checker.verify_compliance.return_value = mock_compliance_result

            result = start_new(incident_id, standard, report_format, export_to_stream=False)

            mock_fetch.assert_called_once_with(incident_id)
            mock_collect.assert_called_once_with(incident_id)
            mock_checker.verify_compliance.assert_called_once_with(mock_incident_data, mock_audit_tracks, standard)
            mock_escalation.assert_not_called()

            self.assertEqual(result["incident_id"], incident_id)
            self.assertEqual(result["compliance_status"], "APPROVED")
            self.assertEqual(result["standard"], standard)
            self.assertEqual(result["checked_items"], checked_items_val)
            self.assertNotIn("stream_data", result)

    def test_start_new_compliance_failed_triggers_escalation_and_export(self):
        incident_id = uuid.uuid4().hex
        standard = uuid.uuid4().hex
        report_format = uuid.uuid4().hex
        
        mock_incident_data = {"id": incident_id, "severity": "HIGH"}
        mock_audit_tracks = [uuid.uuid4().hex]
        mock_violations = [uuid.uuid4().hex, uuid.uuid4().hex]
        mock_compliance_result = {
            "status": "FAILED",
            "violations": mock_violations
        }
        mock_stream_export_result = uuid.uuid4().hex

        with patch('skills.incident_aggregator.fetch_incident_data', return_value=mock_incident_data) as mock_fetch, \
             patch('skills.incident_audit_trail_collector.collect_tracks', return_value=mock_audit_tracks) as mock_collect, \
             patch('skills.incident_forensics_compliance_checker') as mock_checker, \
             patch('skills.incident_auto_escalation_engine.trigger_escalation') as mock_escalation, \
             patch('skills.recovery_report_exporter.export_stream', return_value=mock_stream_export_result) as mock_export:
            
            if hasattr(mock_checker, "verify_compliance"):
                delattr(mock_checker, "verify_compliance")
            if hasattr(mock_checker, "check_compliance"):
                delattr(mock_checker, "check_compliance")
            
            result = start_new(incident_id, standard, report_format, export_to_stream=True)

            mock_fetch.assert_called_once_with(incident_id)
            mock_collect.assert_called_once_with(incident_id)
            mock_escalation.assert_called_once_with(incident_id, mock_compliance_result)
            mock_export.assert_called_once()

            self.assertEqual(result["incident_id"], incident_id)
            self.assertEqual(result["compliance_status"], "FAILED")
            self.assertEqual(result["standard"], standard)
            self.assertEqual(result["violations"], mock_violations)
            self.assertEqual(result["stream_data"], mock_stream_export_result)
            self.assertEqual(result["checked_items"], len(mock_audit_tracks))

    def test_start_new_compliance_fallback_check_compliance(self):
        incident_id = uuid.uuid4().hex
        standard = uuid.uuid4().hex
        report_format = uuid.uuid4().hex
        
        mock_incident_data = {"id": incident_id}
        mock_audit_tracks = [uuid.uuid4().hex, uuid.uuid4().hex, uuid.uuid4().hex]
        checked_items_val = random.randint(30, 50)
        mock_compliance_result = {
            "status": "APPROVED",
            "checked_items": checked_items_val
        }

        with patch('skills.incident_aggregator.fetch_incident_data', return_value=mock_incident_data), \
             patch('skills.incident_audit_trail_collector.collect_tracks', return_value=mock_audit_tracks), \
             patch('skills.incident_forensics_compliance_checker') as mock_checker:
            
            if hasattr(mock_checker, "verify_compliance"):
                delattr(mock_checker, "verify_compliance")
            mock_checker.check_compliance.return_value = mock_compliance_result

            result = start_new(incident_id, standard, report_format, export_to_stream=False)

            mock_checker.check_compliance.assert_called_once_with(mock_incident_data, mock_audit_tracks, standard)
            self.assertEqual(result["checked_items"], checked_items_val)

    def test_generate_compliance_report_writes_file(self):
        aggregated_incidents = {uuid.uuid4().hex: random.randint(1, 100)}
        audit_trail = [uuid.uuid4().hex, uuid.uuid4().hex]
        output_path = os.path.join(uuid.uuid4().hex, uuid.uuid4().hex, f"{uuid.uuid4().hex}.json")
        metadata = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_file = MagicMock()
        with patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', return_value=mock_file) as mock_open:
            
            success = generate_compliance_report(aggregated_incidents, audit_trail, output_path, metadata)

            self.assertTrue(success)
            mock_makedirs.assert_called_once_with(os.path.dirname(output_path), exist_ok=True)
            mock_open.assert_called_once_with(output_path, "w", encoding="utf-8")