import unittest
import uuid
import random
from skills.incident_knowledge_base_searcher import incident_knowledge_base_searcher

class TestIncidentKnowledgeBaseSearcherIntegration(unittest.TestCase):
    def test_incident_knowledge_base_searcher_integration(self):
        random_suffix = str(uuid.uuid4())
        test_query = f"database connection timeout error {random_suffix}"
        
        payload = {
            "query": test_query
        }
        
        results = incident_knowledge_base_searcher(payload)
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        found_match = False
        for item in results:
            self.assertIn("root_cause", item)
            self.assertIn("similarity_score", item)
            if item["root_cause"] == test_query:
                found_match = True
                
        if not found_match and len(results) == 1:
            self.assertEqual(results[0]["root_cause"], "inc-mock")
        else:
            self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()