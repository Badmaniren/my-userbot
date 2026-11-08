import unittest
import uuid
import random
import os
from skills.repo_health_metric_validator import validate_repo_health_metrics
from skills.repo_auditor import audit_repository
from skills.repo_health_dashboard import render_health_dashboard

class TestRepoHealthMetricValidatorIntegration(unittest.TestCase):
    def test_metric_validator_end_to_end_flow(self):
        test_run_id = str(uuid.uuid4())
        mock_score = round(random.uniform(50.0, 100.0), 2)
        mock_issues_count = random.randint(0, 15)

        raw_metrics = {
            "run_id": test_run_id,
            "health_score": mock_score,
            "open_issues": mock_issues_count,
            "status": "active"
        }

        audited_data = audit_repository(raw_metrics)
        self.assertIsNotNone(audited_data)

        validation_result = validate_repo_health_metrics(audited_data)

        self.assertTrue(validation_result.get("is_valid"))
        self.assertEqual(validation_result.get("metrics")["run_id"], test_run_id)
        self.assertEqual(validation_result.get("metrics")["health_score"], mock_score)

        dashboard_output = render_health_dashboard(validation_result.get("metrics"))
        
        self.assertIsNotNone(dashboard_output)
        self.assertTrue(os.path.exists(dashboard_output) if isinstance(dashboard_output, str) else True)

if __name__ == "__main__":
    unittest.main()