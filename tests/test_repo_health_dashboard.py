import unittest
from unittest.mock import patch
import random
import uuid
import string
import io
from skills.repo_health_dashboard import RepoHealthDashboard

class TestRepoHealthDashboard(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.dashboard = RepoHealthDashboard(self.repo_path)

    def test_init_sets_repo_path(self):
        random_path = f"/var/git/{uuid.uuid4().hex}"
        dash = RepoHealthDashboard(random_path)
        self.assertEqual(dash.repo_path, random_path)

    def test_generate_dashboard_returns_dict(self):
        metric_key = f"metric_{uuid.uuid4().hex[:6]}"
        metric_val = random.randint(10, 1000)
        
        with patch('skills.repo_health_dashboard.RepoAuditor') as mock_auditor:
            instance = mock_auditor.return_value
            instance.calculate_metrics.return_value = {metric_key: metric_val}
            
            result = self.dashboard.generate_dashboard()
            self.assertIsInstance(result, dict)
            self.assertIn(metric_key, result)
            self.assertEqual(result[metric_key], metric_val)

    def test_export_dashboard_saves_file(self):
        file_name = f"dash_{uuid.uuid4().hex}.json"
        random_status = random.choice(['HEALTHY', 'CRITICAL', 'WARNING', 'UNKNOWN'])
        
        with patch('skills.repo_health_dashboard.RepoMonitor') as mock_monitor, \
             patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            
            mock_monitor.return_value.check_status.return_value = random_status
            
            res = self.dashboard.export_dashboard(file_name)
            self.assertTrue(res)
            mock_file.assert_called_once_with(file_name, 'w', encoding='utf-8')
            mock_file().write.assert_called()

    def test_process_stream_metrics(self):
        token = uuid.uuid4().hex
        stream_data = f"METRIC:{token}:{random.randint(1, 500)}".encode('utf-8')
        mock_stream = io.BytesIO(stream_data)

        result = self.dashboard.process_stream(mock_stream)
        self.assertIsInstance(result, dict)
        self.assertTrue(any(token in str(k) or token in str(v) for k, v in result.items()))

    def test_render_widget_html(self):
        widget_title = ''.join(random.choices(string.ascii_letters, k=8))
        widget_val = random.randint(1, 100)
        
        html_output = self.dashboard.render_widget(widget_title, widget_val)
        self.assertIsInstance(html_output, str)
        self.assertIn(widget_title, html_output)
        self.assertIn(str(widget_val), html_output)