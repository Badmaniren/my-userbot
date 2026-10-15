import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.hypothesis_generator import HypothesisGenerator, HypothesisGeneratorError


class TestHypothesisGenerator(unittest.TestCase):

    def setUp(self):
        self.rand_repo_path = f"/path/to/repo_{uuid.uuid4().hex[:8]}"
        self.mock_git_inspector = MagicMock()
        self.mock_lesson_parser = MagicMock()
        self.generator = HypothesisGenerator(
            repo_path=self.rand_repo_path,
            git_inspector=self.mock_git_inspector,
            lesson_parser=self.mock_lesson_parser
        )

    def test_init_defaults(self):
        with patch('skills.hypothesis_generator.GitInspector') as mock_git_cls, \
             patch('skills.hypothesis_generator.LessonParser') as mock_lesson_cls:

            gen = HypothesisGenerator(repo_path=self.rand_repo_path)
            self.assertEqual(gen.repo_path, self.rand_repo_path)
            mock_git_cls.assert_called_once_with(repo_path=self.rand_repo_path)
            mock_lesson_cls.assert_called_once()

    def test_generate_hypotheses_success(self):
        max_commits_val = random.randint(1, 50)

        lesson_id = uuid.uuid4().hex
        lesson_title = ''.join(random.choices(string.ascii_letters, k=10))
        lesson_commit = uuid.uuid4().hex
        lesson_content = ''.join(random.choices(string.ascii_letters, k=20))

        commit_hash = uuid.uuid4().hex
        commit_msg = ''.join(random.choices(string.ascii_letters, k=15))

        self.mock_lesson_parser.extract_lessons.return_value = [{
            "id": lesson_id,
            "title": lesson_title,
            "commit": lesson_commit,
            "content": lesson_content
        }]
        self.mock_git_inspector.get_commit_history.return_value = [{
            "hash": commit_hash,
            "message": commit_msg
        }]

        hypotheses = self.generator.generate_hypotheses(max_commits=max_commits_val)

        self.mock_lesson_parser.extract_lessons.assert_called_once_with(max_commits=max_commits_val)
        self.mock_git_inspector.get_commit_history.assert_called_once_with(max_count=max_commits_val)

        self.assertEqual(len(hypotheses), 2)

        self.assertEqual(hypotheses[0]["id"], lesson_id)
        self.assertEqual(hypotheses[0]["title"], lesson_title)
        self.assertEqual(hypotheses[0]["commit"], lesson_commit)
        self.assertEqual(hypotheses[0]["content"], lesson_content)
        self.assertEqual(hypotheses[0]["priority_score"], 10)

        self.assertEqual(hypotheses[1]["id"], commit_hash)
        self.assertEqual(hypotheses[1]["title"], commit_msg)
        self.assertEqual(hypotheses[1]["priority_score"], 5)

    def test_generate_hypotheses_empty(self):
        max_commits_val = random.randint(1, 50)
        self.mock_lesson_parser.extract_lessons.return_value = []
        self.mock_git_inspector.get_commit_history.return_value = []

        hypotheses = self.generator.generate_hypotheses(max_commits=max_commits_val)
        self.assertEqual(hypotheses, [])

    def test_generate_hypotheses_raises_custom_exception(self):
        max_commits_val = random.randint(1, 50)
        err_msg = uuid.uuid4().hex
        self.mock_lesson_parser.extract_lessons.side_effect = Exception(err_msg)

        with self.assertRaises(HypothesisGeneratorError) as ctx:
            self.generator.generate_hypotheses(max_commits=max_commits_val)

        self.assertIn(err_msg, str(ctx.exception))

    def test_generate_hypotheses_preserves_custom_exception(self):
        max_commits_val = random.randint(1, 50)
        err_msg = uuid.uuid4().hex
        self.mock_lesson_parser.extract_lessons.side_effect = HypothesisGeneratorError(err_msg)

        with self.assertRaises(HypothesisGeneratorError) as ctx:
            self.generator.generate_hypotheses(max_commits=max_commits_val)

        self.assertEqual(str(ctx.exception), err_msg)

    def test_analyze_trends(self):
        rand_bytes = bytes(random.getrandbits(8) for _ in range(32))
        dummy_file_path = f"/tmp/{uuid.uuid4().hex}.bin"

        with patch('skills.hypothesis_generator.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value = io.BytesIO(rand_bytes)

            result = self.generator.analyze_trends(dummy_file_path)

            mock_open.assert_called_once_with(dummy_file_path, 'rb')
            self.assertEqual(result, rand_bytes)

    def test_prioritize_hypotheses(self):
        id_1 = uuid.uuid4().hex
        id_2 = uuid.uuid4().hex
        id_3 = uuid.uuid4().hex

        hypotheses = [
            {"id": id_1, "priority_score": 5},
            {"id": id_2, "priority_score": 20},
            {"id": id_3, "priority_score": 10},
        ]

        sorted_hypotheses = self.generator.prioritize_hypotheses(hypotheses)

        self.assertEqual(sorted_hypotheses[0]["id"], id_2)
        self.assertEqual(sorted_hypotheses[0]["priority_score"], 20)
        self.assertEqual(sorted_hypotheses[1]["id"], id_3)
        self.assertEqual(sorted_hypotheses[1]["priority_score"], 10)
        self.assertEqual(sorted_hypotheses[2]["id"], id_1)
        self.assertEqual(sorted_hypotheses[2]["priority_score"], 5)