import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys

from skills.code_optimizer import CodeOptimizer, CodeOptimizerError


class TestCodeOptimizerInquisitor(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.mock_git_inspector = MagicMock()
        self.mock_lesson_parser = MagicMock()
        self.mock_patch_executor = MagicMock()

    def test_optimizer_initialization(self):
        optimizer = CodeOptimizer(
            repo_path=self.repo_path,
            git_inspector=self.mock_git_inspector,
            lesson_parser=self.mock_lesson_parser,
            patch_executor=self.mock_patch_executor
        )
        self.assertEqual(optimizer.repo_path, self.repo_path)
        self.assertEqual(optimizer.git_inspector, self.mock_git_inspector)
        self.assertEqual(optimizer.lesson_parser, self.mock_lesson_parser)
        self.assertEqual(optimizer.patch_executor, self.mock_patch_executor)

    def test_analyze_unused_imports_success(self):
        random_file = f"{uuid.uuid4().hex}.py"
        random_mod = f"mod_{uuid.uuid4().hex}"
        random_import = f"import {random_mod}"
        random_code = f"{random_import}\nprint('{uuid.uuid4().hex}')"

        optimizer = CodeOptimizer(
            repo_path=self.repo_path,
            git_inspector=self.mock_git_inspector,
            lesson_parser=self.mock_lesson_parser,
            patch_executor=self.mock_patch_executor
        )

        with patch("os.path.isfile", return_value=True):
            with patch("builtins.open", unittest.mock.mock_open(read_data=random_code)):
                unused = optimizer.analyze_unused_imports(random_file)
                self.assertIn(random_import, unused)

    def test_optimize_structure_by_metrics_chaos(self):
        random_metric_key = uuid.uuid4().hex
        random_metric_val = random.randint(1, 1000)
        metrics = {random_metric_key: random_metric_val}

        optimizer = CodeOptimizer(
            repo_path=self.repo_path,
            git_inspector=self.mock_git_inspector,
            lesson_parser=self.mock_lesson_parser,
            patch_executor=self.mock_patch_executor
        )

        self.mock_patch_executor.apply_patch.return_value = True

        result = optimizer.optimize_structure(metrics)
        self.assertTrue(result)
        self.mock_patch_executor.apply_patch.assert_called()

    def test_optimize_structure_exception_handling(self):
        random_metric_key = uuid.uuid4().hex
        metrics = {random_metric_key: random.randint(-100, 0)}

        optimizer = CodeOptimizer(
            repo_path=self.repo_path,
            git_inspector=self.mock_git_inspector,
            lesson_parser=self.mock_lesson_parser,
            patch_executor=self.mock_patch_executor
        )

        self.mock_patch_executor.apply_patch.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(CodeOptimizerError):
            optimizer.optimize_structure(metrics)

    def test_full_optimization_cycle(self):
        random_commit = uuid.uuid4().hex
        random_file_path = f"{uuid.uuid4().hex}.py"

        self.mock_git_inspector.get_latest_changes.return_value = [random_file_path]
        self.mock_patch_executor.execute_from_lessons.return_value = {uuid.uuid4().hex: True}

        optimizer = CodeOptimizer(
            repo_path=self.repo_path,
            git_inspector=self.mock_git_inspector,
            lesson_parser=self.mock_lesson_parser,
            patch_executor=self.mock_patch_executor
        )

        with patch("os.path.isfile", return_value=True):
            with patch("builtins.open", unittest.mock.mock_open(read_data=f"import os\n")):
                result = optimizer.run_optimization_pipeline()
                self.assertIsInstance(result, dict)
                self.assertTrue(len(result) > 0)


if __name__ == "__main__":
    unittest.main()
