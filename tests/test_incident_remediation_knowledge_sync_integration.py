import unittest
import uuid
import random
import os
import tempfile
from skills.incident_remediation_knowledge_sync import (
    incident_knowledge_base_searcher,
    vulnerability_patch_orchestrator,
    auto_patch_pipeline
)

class TestIncidentRemediationKnowledgeSyncIntegration(unittest.TestCase):
    def test_sync_knowledge_base_with_patch_system_integration(self):
        random_seed = random.randint(1000, 9999)
        unique_incident_id = f"INC-{uuid.uuid4()}-{random_seed}"
        unique_cve_id = f"CVE-2023-{random.randint(10000, 99999)}"
        
        searcher = incident_knowledge_base_searcher()
        patch_orchestrator = vulnerability_patch_orchestrator()
        pipeline = auto_patch_pipeline()

        kb_search_result = searcher.search(unique_incident_id)
        
        self.assertIsNotNone(kb_search_result, "Knowledge base searcher must return a valid object")

        orchestration_payload = {
            "incident_id": unique_incident_id,
            "vulnerability_id": unique_cve_id,
            "search_context": kb_search_result
        }

        orchestration_result = patch_orchestrator.orchestrate(orchestration_payload)
        self.assertIn("status", orchestration_result, "Orchestrator must return a status")

        pipeline_response = pipeline.execute({
            "incident_id": unique_incident_id,
            "orchestration_data": orchestration_result,
            "random_marker": random_seed
        })

        self.assertIsInstance(pipeline_response, dict, "Pipeline must return a dictionary result")
        self.assertEqual(
            pipeline_response.get("incident_id"), 
            unique_incident_id, 
            "Pipeline must preserve the unique incident ID"
        )
        self.assertIn("patch_executed", pipeline_response, "Pipeline response must indicate execution status")

if __name__ == "__main__":
    unittest.main()