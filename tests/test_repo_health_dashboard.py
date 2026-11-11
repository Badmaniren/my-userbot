import unittest
from unittest.mock import patch, mock_open
import io
import uuid
import random
import string
from skills.repo_health_dashboard import RepoHealthDashboard

class TestRepoHealthDashboard(unittest.TestCase):

    def setUp(self):
        self.random_repo = f"/repo_{uuid.uuid4().hex[:8]}"
        self.dashboard = RepoHealthDashboard(self.random_repo)

    def test_init(self):
        self.assertEqual(self.dashboard.repo_path, self.random_repo)

    def test_generate_dashboard_with_calculate_metrics(self):
        expected_key = f"metric_{uuid.uuid4().hex[:6]}"
        expected_val = random.randint(100, 999)
        mock_metrics = {expected_key: expected_val}

        with patch("skills.repo_health_dashboard.RepoAuditor") as MockAuditor:
            instance = MockAuditor.return_value
            del instance.audit
            instance.calculate_metrics.return_value = mock_metrics

            result = self.dashboard.generate_dashboard()

            MockAuditor.assert_called_once_with(self.random_repo)
            instance.calculate_metrics.assert_called_once()
            self.assertIn(expected_key, result)
            self.assertEqual(result[expected_key], expected_val)

    def test_generate_dashboard_with_audit_dict(self):
        expected_key = f"audit_key_{uuid.uuid4().hex[:6]}"
        expected_val = f"val_{uuid.uuid4().hex[:6]}"
        mock_audit_data = {expected_key: expected_val}

        with patch("skills.repo_health_dashboard.RepoAuditor") as MockAuditor:
            instance = MockAuditor.return_value
            del instance.calculate_metrics
            instance.audit.return_value = mock_audit_data

            result = self.dashboard.generate_dashboard()

            MockAuditor.assert_called_once_with(self.random_repo)
            instance.audit.assert_called_once()
            self.assertEqual(result[expected_key], expected_val)

    def test_generate_dashboard_with_audit_scalar(self):
        scalar_val = f"scalar_{uuid.uuid4().hex[:6]}"

        with patch("skills.repo_health_dashboard.RepoAuditor") as MockAuditor:
            instance = MockAuditor.return_value
            del instance.calculate_metrics
            instance.audit.return_value = scalar_val

            result = self.dashboard.generate_dashboard()

            MockAuditor.assert_called_once_with(self.random_repo)
            self.assertIn("audit_result", result)
            self.assertEqual(result["audit_result"], scalar_val)

    def test_generate_dashboard_fallback(self):
        with patch("skills.repo_health_dashboard.RepoAuditor") as MockAuditor:
            instance = MockAuditor.return_value
            del instance.calculate_metrics
            del instance.audit

            result = self.dashboard.generate_dashboard()

            self.assertEqual(result, {})

    def test_export_dashboard(self):
        random_file = f"/tmp/{uuid.uuid4().hex}.json"
        monitor_status = f"status_{uuid.uuid4().hex[:6]}"
        dashboard_key = f"key_{uuid.uuid4().hex[:6]}"
        dashboard_val = random.randint(1, 100)

        with patch("skills.repo_health_dashboard.RepoMonitor") as MockMonitor, \
             patch.object(RepoHealthDashboard, "generate_dashboard") as mock_gen, \
             patch("builtins.open", mock_open()) as mock_file_open:
            
            monitor_instance = MockMonitor.return_value
            monitor_instance.check_status.return_value = monitor_status
            mock_gen.return_value = {dashboard_key: dashboard_val}

            res = self.dashboard.export_dashboard(random_file)

            self.assertTrue(res)
            MockMonitor.assert_called_once_with(self.random_repo)
            monitor_instance.check_status.assert_called_once()
            mock_gen.assert_called_once()
            mock_file_open.assert_called_once_with(random_file, 'w', encoding='utf-8')

    def test_process_stream_two_parts(self):
        k = f"key_{uuid.uuid4().hex[:5]}"
        v = f"val_{uuid.uuid4().hex[:5]}"
        stream_data = f"{k}:{v}\n".encode('utf-8')
        stream = io.BytesIO(stream_data)

        res = self.dashboard.process_stream(stream)
        self.assertIn(k, res)
        self.assertEqual(res[k], v)

    def test_process_stream_three_parts(self):
        prefix = f"pre_{uuid.uuid4().hex[:4]}"
        k = f"key_{uuid.uuid4().hex[:5]}"
        v = f"val_{uuid.uuid4().hex[:5]}"
        stream_data = f"{prefix}:{k}:{v}\n".encode('utf-8')
        stream = io.BytesIO(stream_data)

        res = self.dashboard.process_stream(stream)
        self.assertIn(k, res)
        self.assertEqual(res[k], v)

    def test_process_stream_fallback(self):
        raw_content = "".join(random.choices(string.ascii_letters, k=25))
        stream_data = raw_content.encode('utf-8')
        stream = io.BytesIO(stream_data)

        res = self.dashboard.process_stream(stream)
        self.assertIn("raw", res)
        self.assertEqual(res["raw"], raw_content)

    def test_render_widget(self):
        title = f"Title_{uuid.uuid4().hex[:6]}"
        val = random.randint(1000, 9999)

        rendered = self.dashboard.render_widget(title, val)

        self.assertIn(title, rendered)
        self.assertIn(str(val), rendered)
        self.assertIn("<div class='widget'>", rendered)
        self.assertIn("<h3>", rendered)
        self.assertIn("<p>", rendered)

if __name__ == '__main__':
    unittest.main()