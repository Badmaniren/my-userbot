import unittest
import uuid
import random
import os
import tempfile

from skills.incident_knowledge_base_searcher import incident_knowledge_base_searcher
from skills.incident_post_mortem_service import incident_post_mortem_service
from skills.incident_aggregator import incident_aggregator

class TestIncidentKnowledgeBaseSearcherIntegration(unittest.TestCase):

    def test_semantic_search_and_root_cause_pipeline(self):
        unique_suffix = uuid.uuid4().hex[:8]
        incident_id = f"inc-{unique_suffix}"
        error_code = f"ERR_{random.randint(1000, 9999)}"
        
        root_causes = [
            "Database connection pool exhaustion due to leaked connections in payment worker.",
            "Redis memory overflow caused by unBounded cache growth.",
            f"Network timeout during inter-service communication with error code {error_code}."
        ]
        selected_root_cause = random.choice(root_causes)
        
        raw_incident_payload = {
            "incident_id": incident_id,
            "title": f"Critical failure in subsystem {unique_suffix}",
            "description": f"The system failed with {error_code}. Root cause analysis points to: {selected_root_cause}",
            "severity": random.choice(["SEV-1", "SEV-2", "SEV-3"]),
            "status": "resolved"
        }

        aggregated_incident = incident_aggregator(raw_incident_payload)
        self.assertIsNotNone(aggregated_incident)

        post_mortem_payload = {
            "incident_id": incident_id,
            "summary": aggregated_incident.get("title", "Default Title"),
            "root_cause": selected_root_cause,
            "resolution": "Applied dynamic patch and increased pool limits.",
            "preventive_actions": ["Implement circuit breaker", "Add telemetry alerts"]
        }
        
        post_mortem_result = incident_post_mortem_service(post_mortem_payload)
        self.assertIn("post_mortem_id", post_mortem_result)

        search_query = f"{error_code} {selected_root_cause[:20]}"
        search_results = incident_knowledge_base_searcher({
            "query": search_query,
            "limit": 5
        })

        self.assertIsInstance(search_results, list)
        
        found = False
        for result in search_results:
            if result.get("incident_id") == incident_id or error_code in str(result):
                found = True
                break
                
        self.assertTrue(found, f"Integration failed: Incident {incident_id} with error {error_code} was not indexed or retrieved by knowledge base searcher.")

if __name__ == "__main__":
    unittest.main()