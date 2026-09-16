import unittest
import uuid
import random
from skills.incident_recovery_time_estimator import IncidentRecoveryTimeEstimator, estimate_recovery_time
from skills import system_health_telemetry_collector

class TestIncidentRecoveryTimeEstimatorIntegration(unittest.TestCase):
    def test_recovery_time_estimation_integration(self):
        random_id = str(uuid.uuid4())
        random_metric = float(random.randint(10, 90))

        aggregated_incident = {
            "id": random_id,
            "metric": random_metric
        }

        telemetry_data = {
            "cpu_load": float(random.randint(20, 80))
        }

        result = estimate_recovery_time(aggregated_incident, telemetry_data)

        self.assertIsInstance(result, dict)
        self.assertIn("incident_id", result)
        self.assertIn("estimated_minutes", result)
        self.assertEqual(result["incident_id"], random_id)
        self.assertIsInstance(result["estimated_minutes"], int)
        self.assertGreater(result["estimated_minutes"], 0)

    def class_estimator_integration(self):
        estimator = IncidentRecoveryTimeEstimator()
        random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        random_id = str(uuid.uuid4())

        try:
            load = estimator._get_current_system_load()
            self.assertIsInstance(load, float)
        except Exception:
            pass

        estimation_result = estimator.estimate(random_id, random_severity)

        self.assertIsInstance(estimation_result, dict)
        self.assertIn("estimated_hours", estimation_result)
        self.assertIn("confidence_score", estimation_result)
        self.assertIsInstance(estimation_result["estimated_hours"], float)
        self.assertIsInstance(estimation_result["confidence_score"], float)
        self.assertGreaterEqual(estimation_result["confidence_score"], 0.0)
        self.assertLessEqual(estimation_result["confidence_score"], 1.0)

if __name__ == "__main__":
    unittest.main()