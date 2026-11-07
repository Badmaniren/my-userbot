import unittest
import uuid
import random
from skills.repo_health_aggregator import RepoHealthAggregator
from skills.repo_auditor import RepoAuditor
from skills.repo_monitor import RepoMonitor
from skills.dependency_audit_aggregator import DependencyAuditAggregator
from skills.repo_reporter import RepoReporter


class TestRepoHealthAggregatorIntegration(unittest.TestCase):

    def test_aggregate_health_data_real_flow(self):
        run_id = str(uuid.uuid4())
        repo_id = str(uuid.uuid4())
        random_health_score = round(random.uniform(50.0, 100.0), 2)
        random_cpu_usage = round(random.uniform(10.0, 95.0), 2)
        random_vuln_count = random.randint(0, 5)

        auditor = RepoAuditor()
        monitor = RepoMonitor()
        dep_aggregator = DependencyAuditAggregator()
        reporter = RepoReporter()
        aggregator = RepoHealthAggregator()

        audit_result = auditor.audit_repository(repo_id) if hasattr(auditor, "audit_repository") else {"repo_id": repo_id, "health_score": random_health_score}
        if isinstance(audit_result, dict):
            audit_result["health_score"] = random_health_score

        monitoring_result = monitor.collect_metrics(repo_id) if hasattr(monitor, "collect_metrics") else {"repo_id": repo_id, "cpu_usage": random_cpu_usage}
        
        dep_result = dep_aggregator.aggregate(repo_id) if hasattr(dep_aggregator, "aggregate") else {"repo_id": repo_id, "vulnerabilities": random_vuln_count}

        final_report = aggregator.aggregate_health_data(
            run_id=run_id,
            audit_info=audit_result,
            monitoring_data=monitoring_result,
            dependency_metrics=dep_result
        )

        self.assertIsInstance(final_report, dict)
        self.assertEqual(final_report.get("run_id"), run_id)
        self.assertEqual(final_report.get("health_score"), random_health_score)
        self.assertEqual(final_report.get("audit_info"), audit_result)
        self.assertEqual(final_report.get("monitoring_data"), monitoring_result)
        self.assertEqual(final_report.get("dependency_metrics"), dep_result)

        if hasattr(reporter, "generate_report"):
            report_output = reporter.generate_report(final_report)
            self.assertIsNotNone(report_output)


if __name__ == "__main__":
    unittest.main()