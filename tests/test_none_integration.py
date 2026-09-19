import unittest
import uuid
import random
import os
from skills.none import epic_completion_proposal_handler
from skills.incident_trend_analyzer import incident_trend_analyzer
from skills.system_risk_evaluator import system_risk_evaluator

class TestEpicCompletionIntegration(unittest.TestCase):
    def test_epic_completion_and_new_direction_integration(self):
        epic_id = f"epic-{uuid.uuid4()}"
        metric_value = random.uniform(85.0, 99.9)
        
        trend_data = incident_trend_analyzer(
            target_metric="system_stability",
            threshold=metric_value
        )
        
        risk_assessment = system_risk_evaluator(
            trend_report=trend_data,
            include_forecast=True
        )
        
        proposal_result = epic_completion_proposal_handler(
            completed_epic_id=epic_id,
            risk_context=risk_assessment,
            generation_seed=random.randint(1, 10000)
        )
        
        self.assertIn("new_direction_id", proposal_result)
        self.assertEqual(proposal_result["source_epic"], epic_id)
        
        artifact_path = proposal_result.get("proposal_file_path")
        if artifact_path:
            self.assertTrue(os.path.exists(artifact_path))
            with open(artifact_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn(epic_id, content)

if __name__ == "__main__":
    unittest.main()