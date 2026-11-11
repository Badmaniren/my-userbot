import unittest
import os
import json
import uuid
import random
from io import BytesIO
from skills.repo_health_dashboard import RepoHealthDashboard
from skills.repo_auditor import RepoAuditor
from skills.repo_monitor import RepoMonitor

class TestRepoHealthDashboardIntegration(unittest.TestCase):
    def setUp(self):
        self.rand_str = str(uuid.uuid4())[:8]
        self.repo_path = f"/tmp/test_repo_{self.rand_str}"
        os.makedirs(self.repo_path, exist_ok=True)
        self.dashboard = RepoHealthDashboard(self.repo_path)

    def tearDown(self):
        if os.path.exists(self.repo_path):
            for root, dirs, files in os.walk(self.repo_path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.repo_path)

        export_file = f"dashboard_{self.rand_str}.json"
        if os.path.exists(export_file):
            os.remove(export_file)

    def test_generate_dashboard_integration(self):
        metric_key = f"metric_{self.rand_str}"
        metric_val = random.randint(100, 999)
        
        test_file = os.path.join(self.repo_path, f"{metric_key}.txt")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(str(metric_val))

        result = self.dashboard.generate_dashboard()
        self.assertIsInstance(result, dict)

    def test_export_dashboard_integration(self):
        export_file = f"dashboard_{self.rand_str}.json"
        
        status_val = f"status_{self.rand_str}"
        monitor_file = os.path.join(self.repo_path, "monitor_state.txt")
        with open(monitor_file, 'w', encoding='utf-8') as f:
            f.write(status_val)

        success = self.dashboard.export_dashboard(export_file)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_file))

        with open(export_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertIn("repo_status", data)
        self.assertEqual(data["repo_status"], monitor_file)

    def test_process_stream_integration(self):
        k1 = f"key1_{self.rand_str}"
        v1 = f"val1_{self.rand_str}"
        stream_data = f"prefix:{k1}:{v1}\n".encode('utf-8')
        stream = BytesIO(stream_data)

        result = self.dashboard.process_stream(stream)
        self.assertIn(k1, result)
        self.assertEqual(result[k1], v1)

    def test_render_widget_integration(self):
        title = f"Title_{self.rand_str}"
        value = random.randint(1000, 9999)
        rendered = self.dashboard.render_widget(title, value)
        
        self.assertIn(title, rendered)
        self.assertIn(str(value), rendered)
        self.assertIn("<div class='widget'>", rendered)

if __name__ == '__main__':
    unittest.main()