import unittest
import os
import uuid
import random
from skills.incident_post_mortem_generator import generate_post_mortem, IncidentPostMortemGenerator
from skills.incident_aggregator import aggregate_incidents
from skills.incident_auto_recovery_dispatcher import dispatch_recovery

try:
    from skills.incident_auto_escalation_engine import evaluate_escalation
except ImportError:
    evaluate_escalation = None

class TestIncidentPostMortemGeneratorIntegration(unittest.TestCase):
    def setUp(self):
        self.incident_id = str(uuid.uuid4())
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.root_cause = f"Root cause analysis token {uuid.uuid4().hex}"
        self.action = f"Recovery action token {uuid.uuid4().hex}"
        self.output_path = f"/tmp/post_mortem_test_{uuid.uuid4().hex}.json"
        self.telemetry_path = f"/tmp/telemetry_test_{uuid.uuid4().hex}.log"

    def tearDown(self):
        for path in [self.output_path, self.telemetry_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_full_post_mortem_integration(self):
        # Подготовка связанных данных через смежные реальные навыки для сквозной интеграции
        aggregator_input = [{"incident_id": self.incident_id, "status": "resolved"}]
        aggregated = aggregate_incidents(aggregator_input)

        recovery_payload = {"incident_id": self.incident_id, "action": self.action}
        recovery_dispatch_result = dispatch_recovery(recovery_payload)

        if evaluate_escalation is not None:
            try:
                evaluate_escalation({"incident_id": self.incident_id, "severity": self.severity})
            except Exception:
                pass

        with open(self.telemetry_path, "w", encoding="utf-8") as f:
            f.write(f"cpu_usage: {random.randint(10, 99)}%\n")
            f.write(f"memory_leak_detected: False\n")

        generation_payload = {
            "incident_id": self.incident_id,
            "aggregation": aggregated,
            "escalation": {
                "severity": self.severity
            },
            "recovery": {
                "root_cause": self.root_cause,
                "action": self.action
            },
            "output_path": self.output_path
        }

        result = generate_post_mortem(generation_payload)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["incident_id"], self.incident_id)

        report = result["report"]
        self.assertEqual(report["incident_id"], self.incident_id)
        self.assertEqual(report["severity"], self.severity)
        self.assertEqual(report["root_cause"], self.root_cause)
        self.assertEqual(report["resolution_steps"], self.action)
        self.assertTrue(os.path.exists(self.output_path))

        generator = IncidentPostMortemGenerator()
        compiled = generator.compile_full_post_mortem(
            escalation_data={"incident_id": self.incident_id, "severity": self.severity},
            recovery_data={"root_cause": self.root_cause, "resolution_steps": self.action},
            telemetry_path=self.telemetry_path
        )

        self.assertIn("telemetry_metrics", compiled)
        self.assertIn("cpu_usage", compiled["telemetry_metrics"])

if __name__ == "__main__":
    unittest.main()