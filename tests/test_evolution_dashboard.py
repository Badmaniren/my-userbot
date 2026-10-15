import unittest
from unittest.mock import MagicMock, patch, mock_open
import io
import json
import random
import uuid
import string

from skills.evolution_dashboard import (
    EvolutionDashboard,
    EvolutionDashboardError
)
from skills.hypothesis_generator import HypothesisGeneratorError

class TestEvolutionDashboard(unittest.TestCase):

    def setUp(self):
        self.git_inspector = MagicMock()
        self.hypothesis_generator = MagicMock()
        self.patch_executor = MagicMock()
        self.lesson_parser = MagicMock()

        self.dashboard = EvolutionDashboard(
            git_inspector=self.git_inspector,
            hypothesis_generator=self.hypothesis_generator,
            patch_executor=self.patch_executor,
            lesson_parser=self.lesson_parser
        )

        self.rand_commit_hash = uuid.uuid4().hex
        self.rand_lesson_id = uuid.uuid4().hex
        self.rand_hypothesis_id = uuid.uuid4().hex
        self.rand_patch_id = uuid.uuid4().hex
        self.rand_filename = f"{uuid.uuid4().hex}.json"

        letters = string.ascii_letters + " "
        self.rand_hypothesis_text = ''.join(random.choices(letters, k=30))

        self.mock_commit_history = [{"commit": self.rand_commit_hash}]
        self.mock_lessons = [{"id": self.rand_lesson_id}]
        self.mock_hypotheses = [{"id": self.rand_hypothesis_id, "text": self.rand_hypothesis_text}]
        self.mock_patch_results = [{"patch_id": self.rand_patch_id, "status": "applied"}]

        self.git_inspector.get_commit_history.return_value = self.mock_commit_history
        self.lesson_parser.parse_lessons.return_value = self.mock_lessons
        self.hypothesis_generator.generate_hypotheses.return_value = self.mock_hypotheses
        self.patch_executor.execute_from_lessons.return_value = self.mock_patch_results

    def test_collect_metrics_success(self):
        metrics = self.dashboard.collect_metrics()
        self.assertEqual(metrics["commit_history"], self.mock_commit_history)
        self.assertEqual(metrics["lessons"], self.mock_lessons)
        self.assertEqual(metrics["hypotheses"], self.mock_hypotheses)
        self.assertEqual(metrics["patch_results"], self.mock_patch_results)

    def test_collect_metrics_integrity(self):
        metrics = self.dashboard.collect_metrics()
        self.assertIn(self.rand_commit_hash, str(metrics["commit_history"]))
        self.assertIn(self.rand_lesson_id, str(metrics["lessons"]))
        self.assertIn(self.rand_hypothesis_text, str(metrics["hypotheses"]))
        self.assertEqual(metrics["hypotheses"][0]["text"], self.rand_hypothesis_text)
        self.assertIn(self.rand_patch_id, str(metrics["patch_results"]))

    def test_collect_metrics_evolution_dashboard_error_passthrough(self):
        rand_err_msg = uuid.uuid4().hex
        self.git_inspector.get_commit_history.side_effect = EvolutionDashboardError(rand_err_msg)

        with self.assertRaises(EvolutionDashboardError) as ctx:
            self.dashboard.collect_metrics()
        self.assertIn(rand_err_msg, str(ctx.exception))

    def test_collect_metrics_generic_exception_wrapping(self):
        rand_err_msg = uuid.uuid4().hex
        self.git_inspector.get_commit_history.side_effect = RuntimeError(rand_err_msg)

        with self.assertRaises(EvolutionDashboardError) as ctx:
            self.dashboard.collect_metrics()
        self.assertIn(rand_err_msg, str(ctx.exception))

    def test_collect_metrics_hypothesis_generator_error(self):
        rand_err_msg = uuid.uuid4().hex
        self.hypothesis_generator.generate_hypotheses.side_effect = HypothesisGeneratorError(rand_err_msg)

        with self.assertRaises(EvolutionDashboardError) as ctx:
            self.dashboard.collect_metrics()
        self.assertIn(rand_err_msg, str(ctx.exception))

    def test_render_dashboard(self):
        rendered = self.dashboard.render_dashboard()
        parsed = json.loads(rendered)
        self.assertEqual(parsed["commit_history"][0]["commit"], self.rand_commit_hash)
        self.assertEqual(parsed["lessons"][0]["id"], self.rand_lesson_id)
        self.assertEqual(parsed["hypotheses"][0]["text"], self.rand_hypothesis_text)
        self.assertEqual(parsed["patch_results"][0]["patch_id"], self.rand_patch_id)

    def test_export_report(self):
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            filename = self.dashboard.export_report(self.rand_filename)
            self.assertEqual(filename, self.rand_filename)
            mock_file.assert_called_once_with(self.rand_filename, 'w', encoding='utf-8')
            handle = mock_file()
            handle.write.assert_called_once()
            written_data = handle.write.call_args[0][0]
            parsed_written = json.loads(written_data)
            self.assertEqual(parsed_written["hypotheses"][0]["id"], self.rand_hypothesis_id)

    def test_stream_metrics(self):
        stream = self.dashboard.stream_metrics()
        self.assertIsInstance(stream, io.BytesIO)
        content = stream.getvalue().decode('utf-8')
        parsed = json.loads(content)
        self.assertEqual(parsed["commit_history"][0]["commit"], self.rand_commit_hash)
        self.assertEqual(parsed["patch_results"][0]["patch_id"], self.rand_patch_id)

    def test_get_evolution_metrics(self):
        metrics = self.dashboard.get_evolution_metrics()
        self.assertIsInstance(metrics, dict)
        self.assertEqual(metrics["lessons"][0]["id"], self.rand_lesson_id)

    def test_get_summary(self):
        summary = self.dashboard.get_summary()
        self.assertIsInstance(summary, dict)
        self.assertEqual(summary["hypotheses"][0]["text"], self.rand_hypothesis_text)