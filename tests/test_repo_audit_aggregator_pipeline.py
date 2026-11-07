import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from skills.repo_audit_aggregator_pipeline import (
    RepoAuditAggregatorPipeline,
    run_audit_aggregation
)

class TestRepoAuditAggregatorPipeline(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.random_output_dir = f"/tmp/out_{uuid.uuid4().hex}"
        self.random_stream_name = f"stream_{uuid.uuid4().hex}.log"
        self.random_export_path = f"/tmp/export_{uuid.uuid4().hex}"
        self.random_filename = f"report_{uuid.uuid4().hex}.json"
        
        self.random_status_msg = f"status_{uuid.uuid4().hex}"
        self.random_synthesize_key = f"key_{uuid.uuid4().hex}"
        self.random_synthesize_val = f"val_{uuid.uuid4().hex}"
        
        self.stream = io.BytesIO(uuid.uuid4().bytes)

    def test_pipeline_initialization(self):
        with patch('skills.repo_audit_aggregator_pipeline.RepoMonitor') as mock_monitor_cls, \
             patch('skills.repo_audit_aggregator_pipeline.RepoAuditSynthesizer') as mock_synth_cls:
            
            pipeline = RepoAuditAggregatorPipeline(
                repository_path=self.random_repo_path,
                output_dir=self.random_output_dir
            )
            
            self.assertEqual(pipeline.repository_path, self.random_repo_path)
            self.assertEqual(pipeline.output_dir, self.random_output_dir)
            mock_monitor_cls.assert_called_once_with(self.random_repo_path)
            mock_synth_cls.assert_called_once()

    def test_run_aggregation_success(self):
        expected_status = f"git_status_{uuid.uuid4().hex}"
        expected_synthesis = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            self.random_synthesize_key: self.random_synthesize_val
        }
        expected_export_path = f"{self.random_export_path}/{uuid.uuid4().hex}"

        with patch('skills.repo_audit_aggregator_pipeline.RepoMonitor') as mock_monitor_cls, \
             patch('skills.repo_audit_aggregator_pipeline.RepoAuditSynthesizer') as mock_synth_cls, \
             patch('skills.repo_audit_aggregator_pipeline.start_new') as mock_start_new:
            
            mock_monitor_instance = mock_monitor_cls.return_value
            mock_monitor_instance.check_status.return_value = expected_status

            mock_synth_instance = mock_synth_cls.return_value
            mock_synth_instance.synthesize.return_value = expected_synthesis
            mock_synth_instance.export_report.return_value = expected_export_path

            pipeline = RepoAuditAggregatorPipeline(
                repository_path=self.random_repo_path,
                output_dir=self.random_output_dir
            )

            result = pipeline.run(export_stream=self.stream, filename=self.random_filename)

            mock_start_new.assert_called_once_with(
                repository_path=self.random_repo_path,
                output_dir=self.random_output_dir,
                export_stream=self.stream
            )

            mock_monitor_instance.check_status.assert_called_once()
            
            mock_synth_instance.synthesize.assert_called_once()
            passed_payload = mock_synth_instance.synthesize.call_args[0][0]
            self.assertEqual(passed_payload["monitor_status"], expected_status)

            mock_synth_instance.export_report.assert_called_once_with(
                target_path=self.random_output_dir,
                synthesis_result=expected_synthesis,
                filename=self.random_filename
            )

            self.assertEqual(result["monitor_status"], expected_status)
            self.assertEqual(result["synthesis"], expected_synthesis)
            self.assertEqual(result["export_path"], expected_export_path)

    def test_run_aggregation_exception_handling(self):
        random_error_msg = f"error_{uuid.uuid4().hex}"

        with patch('skills.repo_audit_aggregator_pipeline.RepoMonitor') as mock_monitor_cls, \
             patch('skills.repo_audit_aggregator_pipeline.RepoAuditSynthesizer'), \
             patch('skills.repo_audit_aggregator_pipeline.start_new') as mock_start_new:
            
            mock_start_new.side_effect = Exception(random_error_msg)

            pipeline = RepoAuditAggregatorPipeline(
                repository_path=self.random_repo_path,
                output_dir=self.random_output_dir
            )

            with self.assertRaises(Exception) as ctx:
                pipeline.run(export_stream=self.stream, filename=self.random_filename)

            self.assertIn(random_error_msg, str(ctx.exception))

    def test_run_audit_aggregation_helper_function(self):
        expected_status = f"status_{uuid.uuid4().hex}"
        expected_synthesis = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_export = f"/var/log/{uuid.uuid4().hex}.json"

        with patch('skills.repo_audit_aggregator_pipeline.RepoMonitor') as mock_monitor_cls, \
             patch('skills.repo_audit_aggregator_pipeline.RepoAuditSynthesizer') as mock_synth_cls, \
             patch('skills.repo_audit_aggregator_pipeline.start_new'):
            
            mock_monitor_cls.return_value.check_status.return_value = expected_status
            mock_synth_cls.return_value.synthesize.return_value = expected_synthesis
            mock_synth_cls.return_value.export_report.return_value = expected_export

            res = run_audit_aggregation(
                repository_path=self.random_repo_path,
                output_dir=self.random_output_dir,
                export_stream=self.stream,
                filename=self.random_filename
            )

            self.assertEqual(res["monitor_status"], expected_status)
            self.assertEqual(res["synthesis"], expected_synthesis)
            self.assertEqual(res["export_path"], expected_export)

if __name__ == '__main__':
    unittest.main()