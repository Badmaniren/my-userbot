import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
from datetime import datetime, timedelta

from skills.incident_sla_tracker import IncidentSLATracker

class TestIncidentSLATracker(unittest.TestCase):
    def setUp(self):
        # Generate random SLA thresholds for testing to prevent hardcoding
        self.severities = [f"SEV_{uuid.uuid4().hex[:4].upper()}" for _ in range(4)]
        self.sla_thresholds = {
            sev: random.randint(1000, 100000) for sev in self.severities
        }
        # Random warning percentage threshold between 50% and 90%
        self.warning_threshold_pct = random.uniform(0.50, 0.90)
        
        self.tracker = IncidentSLATracker(
            sla_thresholds=self.sla_thresholds,
            warning_threshold_pct=self.warning_threshold_pct
        )

    def test_register_incident_and_calculate_remaining_time(self):
        """Ensure incident registration correctly calculates remaining time to SLA breach with random inputs."""
        incident_id = f"inc-{uuid.uuid4().hex}"
        severity = random.choice(self.severities)
        sla_limit = self.sla_thresholds[severity]
        
        # Random elapsed time less than SLA limit
        elapsed = random.randint(10, sla_limit - 10)
        start_time = datetime.now() - timedelta(seconds=elapsed)
        
        self.tracker.register_incident(
            incident_id=incident_id,
            severity=severity,
            created_at=start_time
        )
        
        current_time = datetime.now()
        expected_remaining = sla_limit - (current_time - start_time).total_seconds()
        
        actual_remaining = self.tracker.get_time_to_breach(incident_id, current_time=current_time)
        
        # Assert with a small delta to account for execution time
        self.assertAlmostEqual(actual_remaining, expected_remaining, delta=2.0)

    def test_identify_potential_and_actual_breaches(self):
        """Verify that warning and critical breach states are correctly identified under chaotic conditions."""
        incident_id_warning = f"inc-{uuid.uuid4().hex}"
        incident_id_breached = f"inc-{uuid.uuid4().hex}"
        incident_id_safe = f"inc-{uuid.uuid4().hex}"
        
        severity = random.choice(self.severities)
        sla_limit = self.sla_thresholds[severity]
        
        now = datetime.now()
        
        # Safe incident: elapsed time is very small (e.g., 5% of SLA)
        safe_elapsed = int(sla_limit * 0.05)
        safe_start = now - timedelta(seconds=safe_elapsed)
        
        # Warning incident: elapsed time is between warning threshold and SLA limit
        warning_elapsed = int(sla_limit * (self.warning_threshold_pct + 0.05))
        if warning_elapsed >= sla_limit:
            warning_elapsed = int(sla_limit * (self.warning_threshold_pct + (1 - self.warning_threshold_pct) / 2))
        warning_start = now - timedelta(seconds=warning_elapsed)
        
        # Breached incident: elapsed time exceeds SLA limit
        breached_elapsed = sla_limit + random.randint(10, 100)
        breached_start = now - timedelta(seconds=breached_elapsed)
        
        self.tracker.register_incident(incident_id_safe, severity, safe_start)
        self.tracker.register_incident(incident_id_warning, severity, warning_start)
        self.tracker.register_incident(incident_id_breached, severity, breached_start)
        
        breaches_and_warnings = self.tracker.check_sla_breaches(current_time=now)
        
        # Map results for verification
        status_map = {item["incident_id"]: item["status"] for item in breaches_and_warnings}
        
        self.assertIn(incident_id_warning, status_map)
        self.assertEqual(status_map[incident_id_warning], "WARNING")
        
        self.assertIn(incident_id_breached, status_map)
        self.assertEqual(status_map[incident_id_breached], "BREACHED")
        
        # Safe incident must not be flagged
        self.assertNotIn(incident_id_safe, status_map)

    def test_resolved_incidents_are_ignored(self):
        """Verify that resolved incidents are excluded from SLA tracking."""
        incident_id = f"inc-{uuid.uuid4().hex}"
        severity = random.choice(self.severities)
        sla_limit = self.sla_thresholds[severity]
        
        # Start time that would trigger a breach
        start_time = datetime.now() - timedelta(seconds=sla_limit + 100)
        
        self.tracker.register_incident(incident_id, severity, start_time)
        
        # Resolve the incident before checking SLA status
        resolution_time = start_time + timedelta(seconds=sla_limit - 50)
        resolved_status_name = f"RESOLVED_{uuid.uuid4().hex[:4].upper()}"
        self.tracker.update_incident_status(incident_id, status=resolved_status_name, updated_at=resolution_time)
        
        breaches = self.tracker.check_sla_breaches(current_time=datetime.now())
        status_map = {item["incident_id"]: item["status"] for item in breaches}
        
        self.assertNotIn(incident_id, status_map)

    def test_escalation_and_notification_triggering(self):
        """Test that notification and escalation bridges are invoked with correct random payloads."""
        mock_notification_path = "skills.incident_sla_tracker.incident_notification_bridge"
        mock_escalation_path = "skills.incident_sla_tracker.incident_auto_escalation_engine"
        
        incident_id = f"inc-{uuid.uuid4().hex}"
        severity = random.choice(self.severities)
        sla_limit = self.sla_thresholds[severity]
        
        # Force a breach state
        start_time = datetime.now() - timedelta(seconds=sla_limit + 500)
        
        with patch(mock_notification_path) as mock_notification, \
             patch(mock_escalation_path) as mock_escalation:
            
            self.tracker.register_incident(incident_id, severity, start_time)
            self.tracker.check_sla_breaches(
                current_time=datetime.now(),
                notification_bridge=mock_notification,
                escalation_engine=mock_escalation
            )
            
            # Verify notification was called with the correct random incident ID
            mock_notification.notify_sla_breach.assert_called_once()
            call_args = mock_notification.notify_sla_breach.call_args[1]
            self.assertEqual(call_args.get("incident_id"), incident_id)
            
            # Verify escalation was triggered with correct parameters
            mock_escalation.escalate_incident.assert_called_once()
            escalation_args = mock_escalation.escalate_incident.call_args[1]
            self.assertEqual(escalation_args.get("incident_id"), incident_id)
            self.assertEqual(escalation_args.get("severity"), severity)

    def test_invalid_incident_handling(self):
        """Ensure querying non-existent incidents raises appropriate KeyError."""
        fake_incident_id = f"inc-{uuid.uuid4().hex}"
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(fake_incident_id, current_time=datetime.now())

if __name__ == "__main__":
    unittest.main()