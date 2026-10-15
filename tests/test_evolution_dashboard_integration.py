import unittest
import tempfile
import shutil
import os
import uuid
import random
import json
from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser
from skills.hypothesis_generator import HypothesisGenerator
from skills.patch_executor import PatchExecutor
from skills.evolution_dashboard import EvolutionDashboard, EvolutionDashboardError

class TestEvolutionDashboardIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        self.run_id = str(uuid.uuid4())[:8]
        self.lesson_filename = f"lesson_{self.run_id}.md"
        self.lesson_path = os.path.join(self.repo_path, self.lesson_filename)

        random_metric_val = random.randint(100, 999)
        lesson_content = f"# Lesson {self.run_id}\n- Fix issue #{random_metric_val}"

        with open(self.lesson_path, "w", encoding="utf-8") as f:
            f.write(lesson_content)

        os.system(f"git -C {self.repo_path} init")
        os.system(f"git -C {self.repo_path} config user.name 'Architect Bot'")
        os.system(f"git -C {self.repo_path} config user.email 'architect@bot.com'")
        os.system(f"git -C {self.repo_path} add {self.lesson_filename}")
        os.system(f"git -C {self.repo_path} commit -m 'Add lesson {self.run_id}'")

        self.git_inspector = GitInspector(repo_path=self.repo_path)
        self.lesson_parser = LessonParser(git_inspector=self.git_inspector)
        self.hypothesis_generator = HypothesisGenerator(git_inspector=self.git_inspector, lesson_parser=self.lesson_parser)
        self.patch_executor = PatchExecutor(repo_path=self.repo_path, git_inspector=self.git_inspector, lesson_parser=self.lesson_parser)

        self.dashboard = EvolutionDashboard(
            git_inspector=self.git_inspector,
            hypothesis_generator=self.hypothesis_generator,
            patch_executor=self.patch_executor,
            lesson_parser=self.lesson_parser
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_collect_metrics_integration(self):
        metrics = self.dashboard.collect_metrics()

        self.assertIn("commit_history", metrics)
        self.assertIn("lessons", metrics)
        self.assertIn("hypotheses", metrics)
        self.assertIn("patch_results", metrics)

        commit_history = metrics["commit_history"]
        found_commit = any(self.run_id in str(c) for c in commit_history)
        self.assertTrue(found_commit, f"Commit history should contain reference to run_id {self.run_id}")

    def test_render_and_export_dashboard_integration(self):
        exported_filename = os.path.join(self.repo_path, f"report_{self.run_id}.json")
        result_path = self.dashboard.export_report(exported_filename)

        self.assertEqual(result_path, exported_filename)
        self.assertTrue(os.path.exists(exported_filename))

        with open(exported_filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("commit_history", data)
        self.assertIn("lessons", data)
        self.assertIn("hypotheses", data)
        self.assertIn("patch_results", data)

    def test_stream_metrics_integration(self):
        stream = self.dashboard.stream_metrics()
        content = stream.read().decode("utf-8")

        parsed_data = json.loads(content)
        self.assertIsInstance(parsed_data, dict)
        self.assertIn("lessons", parsed_data)
        self.assertIn("patch_results", parsed_data)

    def test_get_summary_and_evolution_metrics_integration(self):
        summary = self.dashboard.get_summary()
        evolution = self.dashboard.get_evolution_metrics()

        self.assertEqual(summary.keys(), evolution.keys())
        self.assertGreaterEqual(len(summary["commit_history"]), 1)

if __name__ == "__main__":
    unittest.main()