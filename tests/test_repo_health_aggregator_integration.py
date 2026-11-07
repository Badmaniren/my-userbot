import unittest
import uuid
import random
import os
import tempfile
import shutil

from skills.repo_health_aggregator import RepoHealthAggregator
from skills.repo_auditor import RepoAuditor
from skills.repo_monitor import RepoMonitor
from skills.dependency_audit_aggregator import DependencyAuditAggregator
from skills.repo_reporter import RepoReporter


class TestRepoHealthAggregatorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.aggregator = RepoHealthAggregator()
        self.auditor = RepoAuditor()
        self.monitor = RepoMonitor()
        self.dep_aggregator = DependencyAuditAggregator()
        self.reporter = RepoReporter()

        self.run_id = str(uuid.uuid4())
        self.random_metric_value = random.randint(100, 999)
        self.report_filename = f"health_report_{self.run_id}.json"

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_repo_health_aggregation_and_reporting_flow(self):
        metric_payload = {
            "run_id": self.run_id,
            "health_score": self.random_metric_value,
            "target_path": self.test_dir,
            "status": "active"
        }

        audit_result = self.auditor.audit_repository(self.test_dir, metric_payload)
        self.assertIsNotNone(audit_result)

        monitor_data = self.monitor.collect_metrics(self.test_dir)
        self.assertIsInstance(monitor_data, dict)

        dep_data = self.dep_aggregator.aggregate_audit(self.test_dir)
        self.assertIsNotNone(dep_data)

        aggregated_health = self.aggregator.aggregate_health_data(
            run_id=self.run_id,
            audit_info=audit_result,
            monitoring_data=monitor_data,
            dependency_metrics=dep_data
        )

        self.assertIsInstance(aggregated_health, dict)
        self.assertIn("run_id", aggregated_health)
        self.assertEqual(aggregated_health["run_id"], self.run_id)

        report_path = os.path.join(self.test_dir, self.report_filename)
        generation_result = self.reporter.generate_report(
            output_path=report_path,
            data=aggregated_health
        )

        self.assertTrue(os.path.exists(report_path), "Комплексный отчет не был создан на диске.")
        
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.run_id, content, "Случайный ID сессии отсутствует в сгенерированном отчете.")
            self.assertIn(str(self.random_metric_value), content, "Случайные метрики здоровья отсутствуют в отчете.")


if __name__ == "__main__":
    unittest.main()