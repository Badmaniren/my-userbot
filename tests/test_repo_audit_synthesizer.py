import unittest
from unittest.mock import patch
import uuid
import random
import os
import io

from skills.repo_audit_synthesizer import start_new, RepoAuditSynthesizer


class TestRepoAuditSynthesizer(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.random_output_dir = f"/tmp/{uuid.uuid4().hex}"

    def test_start_new_basic_execution(self):
        with patch("skills.repo_audit_synthesizer.repo_auditor") as mock_auditor:
            rand_key = uuid.uuid4().hex
            rand_val = uuid.uuid4().hex
            mock_auditor.scan.return_value = {rand_key: rand_val}

            result = start_new(self.random_repo_path, output_dir=self.random_output_dir, export_stream=True)

            self.assertIn("synthesis_id", result)
            self.assertEqual(result["repository"], self.random_repo_path)
            self.assertEqual(result["output_dir"], self.random_output_dir)
            self.assertEqual(result.get(rand_key), rand_val)
            mock_auditor.scan.assert_called_once_with(self.random_repo_path)

    def test_start_new_handles_exceptions_gracefully(self):
        with patch("skills.repo_audit_synthesizer.repo_auditor") as mock_auditor:
            err_msg = uuid.uuid4().hex
            mock_auditor.scan.side_effect = Exception(err_msg)

            with self.assertRaises(Exception) as ctx:
                start_new(self.random_repo_path)
            
            self.assertEqual(str(ctx.exception), err_msg)

    def test_synthesize_method_data_mapping(self):
        synthesizer = RepoAuditSynthesizer()
        run_id = uuid.uuid4().hex
        security_payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        health_payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        performance_payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        base_audit_payload = {uuid.uuid4().hex: uuid.uuid4().hex}

        payload = {
            "run_id": run_id,
            "security": security_payload,
            "health": health_payload,
            "performance": performance_payload,
            "base_audit": base_audit_payload
        }

        result = synthesizer.synthesize(payload)
        unified_slice = result.get("unified_slice", {})

        self.assertEqual(unified_slice.get("run_id"), run_id)
        self.assertEqual(unified_slice.get("security"), security_payload)
        self.assertEqual(unified_slice.get("health"), health_payload)
        self.assertEqual(unified_slice.get("performance"), performance_payload)
        self.assertEqual(unified_slice.get("base_audit"), base_audit_payload)
        self.assertEqual(unified_slice.get("metrics"), payload)

    def test_export_report_file_creation(self):
        synthesizer = RepoAuditSynthesizer()
        filename = f"{uuid.uuid4().hex}.txt"
        run_id = uuid.uuid4().hex
        synthesis_result = {
            "unified_slice": {
                "run_id": run_id,
                "metrics": {uuid.uuid4().hex: uuid.uuid4().hex}
            }
        }

        os.makedirs(self.random_output_dir, exist_ok=True)
        try:
            full_path = synthesizer.export_report(self.random_output_dir, synthesis_result, filename)
            self.assertTrue(os.path.exists(full_path))
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn(run_id, content)
        finally:
            if os.path.exists(full_path):
                os.remove(full_path)
            if os.path.exists(self.random_output_dir):
                os.rmdir(self.random_output_dir)


class TestRepoAuditSynthesizerIntegration(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/tmp/{uuid.uuid4().hex}"

    def test_synthesize_repository_audit_real_flow(self):
        with patch("skills.repo_audit_synthesizer.repo_auditor") as mock_auditor, \
             patch("skills.repo_audit_synthesizer.repo_performance_profiler_pipeline") as mock_perf, \
             patch("skills.repo_audit_synthesizer.vulnerability_analyzer") as mock_vuln, \
             patch("skills.repo_audit_synthesizer.repo_health_diagnostic") as mock_health, \
             patch("skills.repo_audit_synthesizer.repo_security_gateway") as mock_sec, \
             patch("skills.repo_audit_synthesizer.repo_reporter") as mock_reporter:

            audit_key, audit_val = uuid.uuid4().hex, uuid.uuid4().hex
            perf_key, perf_val = uuid.uuid4().hex, uuid.uuid4().hex
            vuln_key, vuln_val = uuid.uuid4().hex, uuid.uuid4().hex
            health_key, health_val = uuid.uuid4().hex, uuid.uuid4().hex
            sec_key, sec_val = uuid.uuid4().hex, uuid.uuid4().hex

            mock_auditor.scan.return_value = {audit_key: audit_val}
            mock_perf.run_profiler.return_value = {perf_key: perf_val}
            mock_vuln.analyze.return_value = {vuln_key: vuln_val}
            mock_health.diagnose.return_value = {health_key: health_val}
            mock_sec.evaluate.return_value = {sec_key: sec_val}

            result = start_new(self.random_repo_path, export_stream=True)

            self.assertEqual(result.get(audit_key), audit_val)
            self.assertEqual(result.get("performance"), {perf_key: perf_val})
            self.assertEqual(result.get("vulnerability"), {vuln_key: vuln_val})
            self.assertEqual(result.get("health"), {health_key: health_val})
            self.assertEqual(result.get("security_evaluation"), {sec_key: sec_val})
            mock_reporter.export_stream.assert_called_once()

            synthesizer = RepoAuditSynthesizer()
            synth_res = synthesizer.synthesize(result)
            self.assertIn("unified_slice", synth_res)
            self.assertEqual(synth_res["unified_slice"]["metrics"]["repository"], self.random_repo_path)