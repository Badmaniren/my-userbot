import unittest
import tempfile
import os
import uuid
import random
from io import StringIO
from skills.repo_audit_pipeline import RepoAuditPipeline, run_audit_pipeline

class TestRepoAuditPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repository_path = self.test_dir.name
        self.output_dir = tempfile.TemporaryDirectory()
        
        self.random_marker = str(uuid.uuid4())
        self.metric_value = random.randint(100, 999)
        
        dummy_file_path = os.path.join(self.repository_path, f"test_{self.random_marker}.py")
        with open(dummy_file_path, "w", encoding="utf-8") as f:
            f.write(f"# Marker: {self.random_marker}\nvalue = {self.metric_value}\n")

    def tearDown(self):
        self.test_dir.cleanup()
        self.output_dir.cleanup()

    def test_pipeline_execution_integration(self):
        export_stream = StringIO()
        pipeline = RepoAuditPipeline(
            repository_path=self.repository_path,
            output_dir=self.output_dir.name,
            export_stream=export_stream
        } if False else RepoAuditPipeline(
            repository_path=self.repository_path,
            output_dir=self.output_dir.name,
            export_stream=export_stream
        )

        result = pipeline.execute()

        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        
        stream_content = export_stream.getvalue()
        self.assertIsNotNone(stream_content)

    def test_run_audit_pipeline_functional(self):
        export_stream = StringIO()
        result = run_audit_pipeline(
            repository_path=self.repository_path,
            output_dir=self.output_dir.name,
            export_stream=export_stream
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_pipeline_stream_processing(self):
        pipeline = RepoAuditPipeline(
            repository_path=self.repository_path,
            output_dir=self.output_dir.name
        )
        
        stream_data = f"stream_payload_{uuid.uuid4()}"
        pipeline.process_stream(stream_data)
        
        self.assertEqual(pipeline.export_stream, stream_data)

if __name__ == "__main__":
    unittest.main()