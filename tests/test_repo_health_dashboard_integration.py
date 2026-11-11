import unittest
import os
import tempfile
import json
import uuid
import random
from io import BytesIO
from skills.repo_health_dashboard import RepoHealthDashboard
from skills.repo_auditor import RepoAuditor
from skills.repo_monitor import RepoMonitor

class TestRepoHealthDashboardIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.dash = RepoHealthDashboard(self.repo_path)
        self.rand_id = str(uuid.uuid4())
        self.rand_val = random.randint(100, 9999)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_dashboard_integration_flow(self):
        monitor_file = os.path.join(self.repo_path, "monitor_state.txt")
        status_content = f"status:{self.rand_id}:{self.rand_val}"
        with open(monitor_file, "w", encoding="utf-8") as f:
            f.write(status_content)

        export_file = os.path.join(self.repo_path, f"dashboard_{self.rand_id}.json")
        success = self.dash.export_dashboard(export_file)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_file))

        with open(export_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("repo_status", data)
        self.assertEqual(data["repo_status"], monitor_file)

        stream_data = f"INFO:{self.rand_id}:{self.rand_val}\n"
        stream = BytesIO(stream_data.encode("utf-8"))
        stream_result = self.dash.process_stream(stream)
        self.assertIn(self.rand_id, stream_result)
        self.assertEqual(str(stream_result[self.rand_id]), str(self.rand_val))

        widget_title = f"Title-{self.rand_id}"
        widget_html = self.dash.render_widget(widget_title, self.rand_val)
        self.assertIn(widget_title, widget_html)
        self.assertIn(str(self.rand_val), widget_html)

if __name__ == "__main__":
    unittest.main()