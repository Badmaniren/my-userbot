import unittest
import os
import shutil
import uuid
import random
from datetime import datetime

from skills.incident_forensics_synthesizer import synthesize_forensics_report


class TestIncidentForensicsSynthesizerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = f"test_forensics_sandbox_{uuid.uuid4().hex[:8]}"
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_synthesize_forensics_report_integration(self):
        incident_id = f"INC-{random.randint(10000, 99999)}"
        module_name = f"subsystem_{uuid.uuid4().hex[:6]}"
        error_message = f"Critical system failure code {random.randint(500, 599)}"
        traceback_str = "Traceback (most recent call last):\n  File 'core.py', line 42, in run\n    raise SystemError()"
        
        destination_path = os.path.join(self.test_dir, f"audit_trail_{uuid.uuid4().hex[:6]}.json")
        
        incident_data = {
            "id": incident_id,
            "timestamp": datetime.utcnow().isoformat(),
            "component": module_name,
            "severity": random.choice(["HIGH", "CRITICAL", "BLOCKER"]),
            "details": error_message
        }

        report = synthesize_forensics_report(
            incident_data=incident_data,
            module_name=module_name,
            exception_obj=SystemError(error_message),
            traceback_str=traceback_str,
            destination_path=destination_path,
            include_raw_telemetry=True,
            incident_id=incident_id
        )

        self.assertIsInstance(report, dict)
        self.assertIn("aggregation_result", report)
        self.assertIn("audit_trail_path", report)
        
        self.assertTrue(
            os.path.exists(destination_path),
            f"Integration failure: Audit trail file was not created at {destination_path}"
        )
        
        with open(destination_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertTrue(len(file_content) > 0, "Audit trail file is empty")

        agg_result = report.get("aggregation_result")
        self.assertIsNotNone(agg_result, "Aggregation result missing from forensic synthesis")