import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.repo_health_dashboard import RepoHealthDashboard
from skills.repo_auditor import RepoAuditor
from skills.repo_monitor import RepoMonitor
from skills.git_committer import GitCommitter

class TestRepoHealthDashboardIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        # Инициализация git репозитория через системные команды для тестов
        os.system(f"git -C {self.repo_path} init -b main")
        os.system(f"git -C {self.repo_path} config user.name 'Architect Test'")
        os.system(f"git -C {self.repo_path} config user.email 'architect@test.com'")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_dashboard_integration_flow(self):
        unique_file_name = f"service_{uuid.uuid4().hex[:8]}.py"
        file_path = os.path.join(self.repo_path, unique_file_name)
        
        random_code_snippet = f"# Random metric: {random.randint(1000, 9999)}\ndef compute_{uuid.uuid4().hex[:4]}():\n    pass\n"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(random_code_snippet)

        committer = GitCommitter(self.repo_path)
        commit_msg = f"Add feature {uuid.uuid4().hex[:6]}"
        commit_success = committer.commit_changes(unique_file_name, commit_msg)
        self.assertTrue(commit_success, "GitCommitter должен успешно зафиксировать изменения.")

        monitor = RepoMonitor(self.repo_path)
        status_output = monitor.check_status()
        self.assertIsInstance(status_output, str)

        auditor = RepoAuditor(self.repo_path)
        if hasattr(auditor, "calculate_metrics"):
            metrics = auditor.calculate_metrics()
            self.assertIsInstance(metrics, dict)
        elif hasattr(auditor, "audit"):
            audit_res = auditor.audit()
            self.assertIsNotNone(audit_res)

        dashboard = RepoHealthDashboard(self.repo_path)
        
        dashboard_methods = [m for m in dir(dashboard) if callable(getattr(dashboard, m)) and not m.startswith("_")]
        self.assertGreater(len(dashboard_methods), 0, "RepoHealthDashboard должен содержать публичные методы для дашборда")

        report_filename = f"dashboard_report_{uuid.uuid4().hex}.json"
        report_path = os.path.join(self.repo_path, report_filename)
        
        generated_data = None
        for method_name in ["generate_dashboard", "build_dashboard", "get_metrics", "generate_report", "render_dashboard"]:
            if hasattr(dashboard, method_name):
                method = getattr(dashboard, method_name)
                try:
                    generated_data = method()
                    break
                except TypeError:
                    try:
                        generated_data = method(report_path)
                        break
                    except Exception:
                        pass

        if generated_data is None:
            for method_name in dashboard_methods:
                method = getattr(dashboard, method_name)
                try:
                    generated_data = method()
                    break
                except Exception:
                    pass

        self.assertIsNotNone(generated_data, "RepoHealthDashboard должен успешно генерировать данные дашборда без моков.")

if __name__ == "__main__":
    unittest.main()