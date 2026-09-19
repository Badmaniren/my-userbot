import unittest
import uuid
import random
import os
import json
from skills.none import start_new, epic_completion_proposal_handler

class TestEpicCompletionIntegration(unittest.TestCase):
    def test_epic_completion_proposal_handler_integration(self):
        completed_epic_id = f"epic-{uuid.uuid4()}"
        risk_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        risk_context = {
            "risk_level": risk_level,
            "score": random.randint(1, 100)
        }
        generation_seed = random.randint(1000, 99999)

        result = epic_completion_proposal_handler(
            completed_epic_id=completed_epic_id,
            risk_context=risk_context,
            generation_seed=generation_seed
        )

        self.assertIn("new_direction_id", result)
        self.assertIn("source_epic", result)
        self.assertIn("proposal_file_path", result)
        
        self.assertEqual(result["source_epic"], completed_epic_id)
        self.assertTrue(result["new_direction_id"].startswith("dir-"))
        
        file_path = result["proposal_file_path"]
        self.assertEqual(file_path, f"proposal_{completed_epic_id}.txt")
        
        try:
            self.assertTrue(os.path.exists(file_path))
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            self.assertIn(completed_epic_id, content)
            self.assertIn(str(generation_seed), content)
            self.assertIn(json.dumps(risk_context), content)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

if __name__ == "__main__":
    unittest.main()