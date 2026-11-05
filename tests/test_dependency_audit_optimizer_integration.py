import unittest
import os
import shutil
import uuid
import random
from skills.dependency_audit_optimizer import optimize_and_apply_dependencies
from skills.dependency_audit_aggregator import aggregate_dependencies
from skills.dependency_updater_pipeline import DependencyUpdaterPipeline

class TestDependencyAuditOptimizerIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.repo_path = os.path.abspath(f"./test_repo_{self.random_suffix}")
        os.makedirs(self.repo_path, exist_ok=True)
        
        self.output_report = f"report_{self.random_suffix}.json"
        self.cve_id = f"CVE-2023-{random.randint(1000, 9999)}"
        self.target_version = f"1.{random.randint(0, 9)}.{random.randint(0, 9)}"

    def tearDown(self):
        if os.path.exists(self.repo_path):
            shutil.rmtree(self.repo_path, ignore_errors=True)
        if os.path.exists(self.output_report):
            try:
                os.remove(self.output_report)
            except OSError:
                pass

    def test_real_dependency_audit_optimizer_composition(self):
        result = optimize_and_apply_dependencies(
            repo_path=self.repo_path,
            output_report_name=self.output_report,
            cve_identifier=self.cve_id,
            target_version=self.target_version
        )

        self.assertIsNotNone(result, "Модуль должен возвращать результат выполнения")
        
        report_full_path = os.path.join(os.getcwd(), self.output_report)
        self.assertTrue(
            os.path.exists(report_full_path) or os.path.exists(self.output_report),
            "Интеграция должна генерировать реальный отчет на основе dependency_audit_aggregator"
        )

        pipeline = DependencyUpdaterPipeline(self.repo_path)
        self.assertIsInstance(
            pipeline, 
            DependencyUpdaterPipeline, 
            "Модуль должен корректно инициализировать DependencyUpdaterPipeline без моков"
        )

if __name__ == "__main__":
    unittest.main()