import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.repo_audit_collector import RepoAuditCollector
from skills.repo_auditor import RepoAuditor
from skills.repo_audit_synthesizer import RepoAuditSynthesizer


class TestRepoAuditCollectorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()
        
        self.unique_id = str(uuid.uuid4())
        self.random_metric_value = random.randint(100, 999)
        
        self.dummy_file_name = f"test_source_{self.unique_id}.py"
        dummy_file_path = os.path.join(self.test_dir, self.dummy_file_name)
        
        with open(dummy_file_path, "w", encoding="utf-8") as f:
            f.write(f"# Unique test token: {self.unique_id}\n")
            f.write(f"METRIC_SEED = {self.random_metric_value}\n")
            f.write("def sample_function():\n    pass\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_repo_audit_collector_composition(self):
        collector = RepoAuditCollector(repository_path=self.test_dir, output_dir=self.output_dir)
        
        self.assertIsInstance(collector.auditor, RepoAuditor)
        self.assertIsInstance(collector.synthesizer, RepoAuditSynthesizer)

        collected_data = collector.collect_and_aggregate()

        self.assertIsInstance(collected_data, dict)
        self.assertIn("audit_metrics", collected_data)
        self.assertIn("synthesis_result", collected_data)

        export_filename = f"report_{self.unique_id}.json"
        export_path = collector.export_aggregated_report(filename=export_filename)

        self.assertTrue(os.path.exists(export_path))
        self.assertTrue(export_path.endswith(export_filename))

        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.unique_id, content)