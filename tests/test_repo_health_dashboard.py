import unittest
from unittest.mock import patch, MagicMock
import io
import os
import json
import uuid
import random
import string
from skills.repo_health_dashboard import RepoHealthDashboard

class TestRepoHealthDashboard(unittest.TestCase):
    def setUp(self):
        self.random_repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.dashboard = RepoHealthDashboard(self.random_repo_path)

    def test_init(self):
        self.assertEqual(self.dashboard.repo_path, self.random_repo_path)

    def test_generate_dashboard_with_calculate_metrics(self):
        expected_key = uuid.uuid4().hex
        expected_val = random.randint(100, 999)
        mock_metrics = {expected_key: expected_val}

        with patch("skills.repo_health_dashboard.RepoAuditor") as mock_auditor_cls:
            mock_auditor = mock_auditor_cls.return_value
            del mock_auditor.audit
            mock_auditor.calculate_metrics = MagicMock(return_value=mock_metrics)

            res = self.dashboard.generate_dashboard()
            self.assertEqual(res, mock_metrics)
            mock_auditor.calculate_metrics.assert_called_once()

    def test_generate_dashboard_with_audit_dict(self):
        expected_key = uuid.uuid4().hex
        expected_val = uuid.uuid4().hex
        mock_audit_res = {expected_key: expected_val}

        with patch("skills.repo_health_dashboard.RepoAuditor") as mock_auditor_cls:
            mock_auditor = mock_auditor_cls.return_value
            if hasattr(mock_auditor, "calculate_metrics"):
                del mock_auditor.calculate_metrics
            mock_auditor.audit = MagicMock(return_value=mock_audit_res)

            res = self.dashboard.generate_dashboard()
            self.assertEqual(res, mock_audit_res)
            mock_auditor.audit.assert_called_once()

    def test_generate_dashboard_with_audit_scalar(self):
        scalar_val = uuid.uuid4().hex

        with patch("skills.repo_health_dashboard.RepoAuditor") as mock_auditor_cls:
            mock_auditor = mock_auditor_cls.return_value
            if hasattr(mock_auditor, "calculate_metrics"):
                del mock_auditor.calculate_metrics
            mock_auditor.audit = MagicMock(return_value=scalar_val)

            res = self.dashboard.generate_dashboard()
            self.assertEqual(res, {"audit_result": scalar_val})
            mock_auditor.audit.assert_called_once()

    def test_generate_dashboard_empty(self):
        with patch("skills.repo_health_dashboard.RepoAuditor") as mock_auditor_cls:
            mock_auditor = mock_auditor_cls.return_value
            if hasattr(mock_auditor, "calculate_metrics"):
                del mock_auditor.calculate_metrics
            if hasattr(mock_auditor, "audit"):
                del mock_auditor.audit

            res = self.dashboard.generate_dashboard()
            self.assertEqual(res, {})

    def test_export_dashboard(self):
        status_val = uuid.uuid4().hex
        file_path = f"/tmp/{uuid.uuid4().hex}.json"
        dashboard_data = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch("skills.repo_health_dashboard.RepoMonitor") as mock_monitor_cls, \
             patch.object(self.dashboard, "generate_dashboard", return_value=dashboard_data), \
             patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            
            mock_monitor = mock_monitor_cls.return_value
            mock_monitor.check_status.return_value = status_val

            success = self.dashboard.export_dashboard(file_path)
            self.assertTrue(success)
            mock_file.assert_called_once_with(file_path, 'w', encoding='utf-8')
            
            expected_data = dashboard_data.copy()
            expected_data["repo_status"] = status_val
            
            handle = mock_file()
            written_content = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed_json = json.loads(written_content)
            self.assertEqual(parsed_json, expected_data)

    def test_export_dashboard_fallback_monitor_file(self):
        file_path = f"/tmp/{uuid.uuid4().hex}.json"
        dashboard_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        monitor_file_path = os.path.join(self.random_repo_path, "monitor_state.txt")

        with patch("skills.repo_health_dashboard.RepoMonitor") as mock_monitor_cls, \
             patch.object(self.dashboard, "generate_dashboard", return_value=dashboard_data), \
             patch("os.path.exists", return_value=True), \
             patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            
            mock_monitor = mock_monitor_cls.return_value
            mock_monitor.check_status.return_value = ""

            success = self.dashboard.export_dashboard(file_path)
            self.assertTrue(success)

            expected_data = dashboard_data.copy()
            expected_data["repo_status"] = monitor_file_path

            handle = mock_file()
            written_content = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed_json = json.loads(written_content)
            self.assertEqual(parsed_json, expected_data)

    def test_process_stream_three_parts(self):
        k1, k2 = uuid.uuid4().hex, uuid.uuid4().hex
        v1, v2 = uuid.uuid4().hex, uuid.uuid4().hex
        line = f"PREFIX:{k1}:{k2}:{v1}:{v2}"
        # process_stream splits by ':' and takes parts[1] and parts[2]
        stream_content = line.encode('utf-8')
        stream = io.BytesIO(stream_content)

        res = self.dashboard.process_stream(stream)
        self.assertEqual(res, {k1: k2})

    def test_process_stream_two_parts(self):
        k = uuid.uuid4().hex
        v = uuid.uuid4().hex
        line = f"{k}:{v}"
        stream_content = line.encode('utf-8')
        stream = io.BytesIO(stream_content)

        res = self.dashboard.process_stream(stream)
        self.assertEqual(res, {k: v})

    def test_process_stream_raw(self):
        raw_text = "".join(random.choices(string.ascii_letters, k=25))
        stream = io.BytesIO(raw_text.encode('utf-8'))

        res = self.dashboard.process_stream(stream)
        self.assertEqual(res, {"raw": raw_text})

    def test_render_widget(self):
        title = uuid.uuid4().hex
        val = uuid.uuid4().hex
        html = self.dashboard.render_widget(title, val)
        self.assertIn(title, html)
        self.assertIn(str(val), html)
        self.assertIn("<div class='widget'>", html)
        self.assertIn("<h3>", html)
        self.assertIn("<p>", html)