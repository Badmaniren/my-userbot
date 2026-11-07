import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string

from skills.repo_audit_dispatcher import RepoAuditDispatcher


class TestRepoAuditDispatcher(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.output_dir = f"/tmp/output_{uuid.uuid4().hex}"
        self.export_stream = io.BytesIO(uuid.uuid4().bytes)
        self.dispatcher = RepoAuditDispatcher(
            repository_path=self.repo_path,
            output_dir=self.output_dir,
            export_stream=self.export_stream
        )

    def test_initialization_and_composition(self):
        self.assertEqual(self.dispatcher.repository_path, self.repo_path)
        self.assertEqual(self.dispatcher.output_dir, self.output_dir)
        self.assertEqual(self.dispatcher.export_stream, self.export_stream)
        
        self.assertIsNotNone(self.dispatcher.health_dispatcher)
        self.assertIsNotNone(self.dispatcher.synthesizer)

    def test_dispatch_full_audit_cycle_success(self):
        random_file_path = f"src/{uuid.uuid4().hex}.py"
        random_title = f"Alert_{uuid.uuid4().hex[:8]}"
        random_value = random.randint(1, 1000)
        
        synthetic_payload = {
            "audit_id": uuid.uuid4().hex,
            "status": random.choice(["passed", "warning", "critical"]),
            "score": random.uniform(0.0, 100.0)
        }
        
        expected_synthesis_result = {
            "report_id": uuid.uuid4().hex,
            "data": synthetic_payload
        }
        
        export_filename = f"{uuid.uuid4().hex}.json"
        expected_export_path = f"{self.output_dir}/{export_filename}"

        with patch("skills.repo_audit_dispatcher.RepoHealthDispatcher") as MockHealthDispatcher, \
             patch("skills.repo_audit_dispatcher.RepoAuditSynthesizer") as MockSynthesizerClass:
            
            mock_health_instance = MockHealthDispatcher.return_value
            mock_health_instance.dispatch.return_value = True
            mock_health_instance.dispatch_health_and_notify.return_value = True
            mock_health_instance.check_and_notify_critical.return_value = True

            mock_synth_instance = MockSynthesizerClass.return_value
            mock_synth_instance.synthesize.return_value = expected_synthesis_result
            mock_synth_instance.export_report.return_value = expected_export_path

            dispatcher = RepoAuditDispatcher(
                repository_path=self.repo_path,
                output_dir=self.output_dir,
                export_stream=self.export_stream
            )

            health_result = dispatcher.dispatch_health_checks(random_file_path)
            self.assertTrue(health_result)
            mock_health_instance.dispatch.assert_called_once()

            critical_result = dispatcher.dispatch_critical_check(random_title, random_value, random_file_path)
            self.assertTrue(critical_result)
            mock_health_instance.check_and_notify_critical.assert_called_once_with(random_title, random_value, random_file_path)

            synthesis_result = dispatcher.run_synthesis(synthetic_payload)
            self.assertEqual(synthesis_result, expected_synthesis_result)
            mock_synth_instance.synthesize.assert_called_once_with(synthetic_payload)

            export_result = dispatcher.export_audit_report(expected_synthesis_result, export_filename)
            self.assertEqual(export_result, expected_export_path)
            mock_synth_instance.export_report.assert_called_once_with(self.output_dir, expected_synthesis_result, export_filename)

    def test_run_complete_workflow(self):
        random_file = f"tests/{uuid.uuid4().hex}.py"
        random_payload_key = uuid.uuid4().hex
        random_payload_val = uuid.uuid4().hex
        
        payload = {random_payload_key: random_payload_val}
        export_name = f"report_{uuid.uuid4().hex}.log"
        expected_path = f"{self.output_dir}/{export_name}"

        with patch("skills.repo_health_dispatcher.RepoHealthDispatcher.dispatch", return_value=True) as mock_dispatch, \
             patch("skills.repo_audit_synthesizer.RepoAuditSynthesizer.synthesize", return_value=payload) as mock_synthesize, \
             patch("skills.repo_audit_synthesizer.RepoAuditSynthesizer.export_report", return_value=expected_path) as mock_export:
            
            result = self.dispatcher.run_complete_audit_workflow(random_file, payload, export_name)
            
            self.assertTrue(result["health_dispatched"])
            self.assertEqual(result["synthesis_data"], payload)
            self.assertEqual(result["export_path"], expected_path)
            
            mock_dispatch.assert_called()
            mock_synthesize.assert_called_with(payload)
            mock_export.assert_called_with(self.output_dir, payload, export_name)

    def test_health_stream_processing(self):
        stream_data = ''.join(random.choices(string.ascii_letters + string.digits, k=128)).encode('utf-8')
        mock_stream = io.BytesIO(stream_data)
        random_file = f"lib/{uuid.uuid4().hex}.rs"

        with patch("skills.repo_audit_dispatcher.RepoHealthDispatcher") as MockHealthDispatcher:
            mock_health_instance = MockHealthDispatcher.return_value
            mock_health_instance.process_stream_and_dispatch.return_value = True

            dispatcher = RepoAuditDispatcher(
                repository_path=self.repo_path,
                output_dir=self.output_dir,
                export_stream=self.export_stream
            )

            res = dispatcher.process_audit_stream(mock_stream, random_file)
            self.assertTrue(res)
            mock_health_instance.process_stream_and_dispatch.assert_called_once_with(mock_stream, random_file)


if __name__ == "__main__":
    unittest.main()