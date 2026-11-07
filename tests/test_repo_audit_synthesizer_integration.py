import unittest
import uuid
import os
import tempfile
import random

from skills import repo_audit_synthesizer
from skills import repo_auditor
from skills import repo_performance_profiler_pipeline
from skills import repo_health_diagnostic
from skills import vulnerability_analyzer
from skills import repo_security_gateway
from skills import repo_reporter


class TestRepoAuditSynthesizerIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repository_path = self.temp_dir.name
        self.random_suffix = str(uuid.uuid4())[:8]

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_start_new_integration(self):
        output_dir = os.path.join(self.repository_path, f"output_{self.random_suffix}")
        os.makedirs(output_dir, exist_ok=True)

        result = repo_audit_synthesizer.start_new(
            repository_path=self.repository_path,
            output_dir=output_dir,
            export_stream=True
        )

        self.assertIsInstance(result, dict)
        self.assertIn("synthesis_id", result)
        self.assertIn("repository", result)
        self.assertEqual(result["repository"], self.repository_path)
        self.assertEqual(result.get("output_dir"), output_dir)

        # Проверка что реальные суб-модули отработали и вернули структуры данных (если они реализованы)
        if repo_auditor and hasattr(repo_auditor, "scan"):
            pass
        if repo_performance_profiler_pipeline and hasattr(repo_performance_profiler_pipeline, "run_profiler"):
            self.assertIn("performance", result)
        if vulnerability_analyzer and hasattr(vulnerability_analyzer, "analyze"):
            self.assertIn("vulnerability", result)
        if repo_health_diagnostic and hasattr(repo_health_diagnostic, "diagnose"):
            self.assertIn("health", result)
        if repo_security_gateway and hasattr(repo_security_gateway, "evaluate"):
            self.assertIn("security_evaluation", result)

    def test_repo_audit_synthesizer_class_flow(self):
        synthesizer = repo_audit_synthesizer.RepoAuditSynthesizer()
        
        run_id = f"run-{uuid.uuid4()}"
        random_score = random.randint(1, 100)
        
        payload = {
            "run_id": run_id,
            "security": {"score": random_score, "status": "passed"},
            "health": {"issues": []},
            "performance": {"latency_ms": 42.5},
            "base_audit": {"files_scanned": 10}
        }

        synthesis_result = synthesizer.synthesize(payload)
        
        self.assertIsInstance(synthesis_result, dict)
        self.assertIn("unified_slice", synthesis_result)
        
        unified = synthesis_result["unified_slice"]
        self.assertEqual(unified["run_id"], run_id)
        self.assertEqual(unified["security"]["score"], random_score)

        filename = f"report_{self.random_suffix}.txt"
        exported_file_path = synthesizer.export_report(
            target_path=self.repository_path,
            synthesis_result=synthesis_result,
            filename=filename
        )

        self.assertTrue(os.path.exists(exported_file_path))
        
        with open(exported_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertIn(run_id, content)
        self.assertIn(str(random_score), content)


if __name__ == "__main__":
    unittest.main()