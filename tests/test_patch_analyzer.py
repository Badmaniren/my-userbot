import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

from skills.patch_analyzer import start_new

class TestPatchAnalyzerInquisitor(unittest.TestCase):
    
    def setUp(self):
        self.random_patch_id = uuid.uuid4().hex
        self.random_repo_path = f"/var/repo/{uuid.uuid4().hex}"
        self.random_commit = uuid.uuid4().hex[:8]
        self.random_error_msg = "".join(random.choices(string.ascii_letters + string.space, k=32))
        
    def test_start_new_success_flow(self):
        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = {
            "status": "secure",
            "patch_id": self.random_patch_id,
            "metrics": random.randint(100, 999)
        }
        
        with patch("skills.patch_analyzer.AutonomousEngine", autospec=True) as mock_engine_cls, \
             patch("skills.patch_analyzer.GitInspector", autospec=True) as mock_inspector_cls:
            
            mock_engine = mock_engine_cls.return_value
            mock_engine.run_analysis.return_value = mock_pipeline.execute.return_value
            
            mock_inspector = mock_inspector_cls.return_value
            mock_inspector.get_latest_changes.return_value = io.BytesIO(self.random_error_msg.encode('utf-8'))
            
            result = start_new(self.random_repo_path)
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("patch_id"), self.random_patch_id)
            self.assertEqual(result.get("status"), "secure")
            mock_engine_cls.assert_called_once()
            mock_inspector_cls.assert_called_once_with(repo_path=self.random_repo_path)

    def test_start_new_anomaly_detected_raises_exception(self):
        from skills.patch_analyzer import AutonomousEngineError
        
        with patch("skills.patch_analyzer.AutonomousEngine", autospec=True) as mock_engine_cls:
            mock_engine = mock_engine_cls.return_value
            mock_engine.run_analysis.side_effect = AutonomousEngineError(self.random_error_msg)
            
            with self.assertRaises(AutonomousEngineError) as ctx:
                start_new(self.random_repo_path)
                
            self.assertIn(self.random_error_msg, str(ctx.exception))

    def test_start_new_git_inspection_failure(self):
        from skills.patch_analyzer import CodeSanitizerError
        
        with patch("skills.patch_analyzer.GitInspector", autospec=True) as mock_inspector_cls, \
             patch("skills.patch_analyzer.CodeSanitizer", autospec=True) as mock_sanitizer_cls:
            
            mock_inspector = mock_inspector_cls.return_value
            mock_inspector.get_file_diff.side_effect = Exception(self.random_error_msg)
            
            with self.assertRaises(Exception) as ctx:
                start_new(self.random_repo_path)
                
            self.assertEqual(str(ctx.exception), self.random_error_msg)

    def test_start_new_with_random_telemetry_payload(self):
        random_telemetry_data = {
            "node_id": uuid.uuid4().hex,
            "load": random.uniform(0.1, 0.9),
            "signature": "".join(random.choices(string.hexdigits, k=16))
        }
        
        with patch("skills.patch_analyzer.SystemTelemetry", autospec=True) as mock_telemetry_cls, \
             patch("skills.patch_analyzer.AutonomousEngine", autospec=True) as mock_engine_cls:
            
            mock_telemetry = mock_telemetry_cls.return_value
            mock_telemetry.collect.return_value = random_telemetry_data
            
            mock_engine = mock_engine_cls.return_value
            mock_engine.evaluate_telemetry.return_value = True
            
            result = start_new(self.random_repo_path)
            
            self.assertIsNotNone(result)
            mock_telemetry.collect.assert_called_once()

    def test_start_new_hypothesis_generator_integration(self):
        random_hypothesis_id = uuid.uuid4().hex
        
        with patch("skills.patch_analyzer.HypothesisGenerator", autospec=True) as mock_hyp_cls, \
             patch("skills.patch_analyzer.PatchVerifier", autospec=True) as mock_verifier_cls:
            
            mock_hyp = mock_hyp_cls.return_value
            mock_hyp.generate.return_value = {"id": random_hypothesis_id, "risk": random.choice(["HIGH", "CRITICAL", "LOW"])}
            
            mock_verifier = mock_verifier_cls.return_value
            mock_verifier.verify.return_value = True
            
            res = start_new(self.random_repo_path)
            
            mock_hyp.generate.assert_called()
            mock_verifier.verify.assert_called()

if __name__ == "__main__":
    unittest.main()