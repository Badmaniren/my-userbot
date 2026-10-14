import io
import re
import uuid
import random
import unittest
from unittest.mock import MagicMock, patch
import requests

from skills.hypothesis_generator import HypothesisGenerator, HypothesisError, GitInspectorStubOrSimilar
from skills.lesson_parser import LessonParserError


class TestHypothesisGenerator(unittest.TestCase):

    def setUp(self):
        self.mock_git_inspector = MagicMock()
        self.mock_lesson_parser = MagicMock()
        self.generator = HypothesisGenerator(
            git_inspector=self.mock_git_inspector,
            lesson_parser=self.mock_lesson_parser
        )

    def test_init_reverse_arguments_order(self):
        rand_str_1 = uuid.uuid4().hex
        rand_str_2 = uuid.uuid4().hex
        stub = GitInspectorStubOrSimilar()

        gen = HypothesisGenerator(stub, lesson_parser=self.mock_lesson_parser)
        self.assertEqual(gen.git_inspector, self.mock_lesson_parser)
        self.assertEqual(gen.lesson_parser, stub)

        gen_alt = HypothesisGenerator(self.mock_git_inspector, lesson_parser=stub)
        self.assertEqual(gen_alt.git_inspector, self.mock_git_inspector)
        self.assertEqual(gen_alt.lesson_parser, stub)

    def test_generate_hypotheses_parser_error(self):
        rand_msg = uuid.uuid4().hex
        self.mock_lesson_parser.parse_lessons.side_effect = LessonParserError(rand_msg)
        max_c = random.randint(1, 50)

        with self.assertRaises(HypothesisError) as ctx:
            self.generator.generate_hypotheses(max_commits=max_c)

        self.assertIn(rand_msg, str(ctx.exception))
        self.mock_lesson_parser.parse_lessons.assert_called_once_with(max_commits=max_c)

    def test_generate_hypotheses_empty_lessons(self):
        self.mock_lesson_parser.parse_lessons.return_value = []
        res = self.generator.generate_hypotheses()
        self.assertEqual(res, [])

    @patch("skills.hypothesis_generator.requests.post")
    def test_generate_hypotheses_success_api(self, mock_post):
        lesson_id = uuid.uuid4().hex
        commit_hash = uuid.uuid4().hex
        title = uuid.uuid4().hex
        insight = uuid.uuid4().hex
        api_id = uuid.uuid4().hex
        hyp_text = uuid.uuid4().hex

        lesson_item = {
            "id": lesson_id,
            "commit_hash": commit_hash,
            "title": title,
            "insight": insight
        }
        self.mock_lesson_parser.parse_lessons.return_value = [lesson_item]

        rand_diff = f"+var_{uuid.uuid4().hex[:4]} = {random.randint(100, 999)}"
        self.mock_git_inspector.get_file_diff.return_value = rand_diff

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": api_id,
            "hypothesis": hyp_text
        }
        mock_post.return_value = mock_response

        results = self.generator.generate_hypotheses()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["lesson_id"], lesson_id)
        self.assertEqual(results[0]["hypothesis"], hyp_text)
        self.assertEqual(results[0]["api_response_id"], api_id)
        self.assertEqual(results[0]["title"], title)
        self.assertEqual(results[0]["insight"], insight)

        mock_post.assert_called_once()
        self.mock_git_inspector.get_file_diff.assert_called_once_with(commit_hash)

    @patch("skills.hypothesis_generator.requests.post")
    def test_generate_hypotheses_api_failure_fallback(self, mock_post):
        lesson_id = uuid.uuid4().hex
        commit_hash = uuid.uuid4().hex
        title = uuid.uuid4().hex
        insight = uuid.uuid4().hex

        lesson_item = {
            "id": lesson_id,
            "commit_hash": commit_hash,
            "title": title,
            "insight": insight
        }
        self.mock_lesson_parser.parse_lessons.return_value = [lesson_item]
        self.mock_git_inspector.get_file_diff.side_effect = Exception(uuid.uuid4().hex)

        mock_post.side_effect = requests.RequestException(uuid.uuid4().hex)

        results = self.generator.generate_hypotheses()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["lesson_id"], lesson_id)
        self.assertIn(title, results[0]["hypothesis"])
        self.assertIn(insight, results[0]["hypothesis"])
        self.assertIn(commit_hash, results[0]["hypothesis"])
        self.assertEqual(results[0]["api_response_id"], lesson_id)

    def test_analyze_file_snapshot_bytes_io(self):
        commit_hash = uuid.uuid4().hex
        file_path = uuid.uuid4().hex
        random_content = uuid.uuid4().hex.encode("utf-8")

        stream = io.BytesIO(random_content)
        self.mock_git_inspector.read_file_at_commit.return_value = stream

        decoded = self.generator.analyze_file_snapshot(commit_hash, file_path)
        self.assertEqual(decoded, random_content.decode("utf-8"))
        self.mock_git_inspector.read_file_at_commit.assert_called_once_with(commit_hash, file_path)

    def test_analyze_file_snapshot_general_stream(self):
        commit_hash = uuid.uuid4().hex
        file_path = uuid.uuid4().hex
        random_text = uuid.uuid4().hex

        mock_stream = MagicMock()
        mock_stream.read.return_value = random_text
        self.mock_git_inspector.read_file_at_commit.return_value = mock_stream

        result = self.generator.analyze_file_snapshot(commit_hash, file_path)
        self.assertEqual(result, random_text)

    def test_analyze_file_snapshot_other_type(self):
        commit_hash = uuid.uuid4().hex
        file_path = uuid.uuid4().hex
        random_num = random.randint(1000, 99999)

        self.mock_git_inspector.read_file_at_commit.return_value = random_num

        result = self.generator.analyze_file_snapshot(commit_hash, file_path)
        self.assertEqual(result, str(random_num))

    def test_extract_metrics_from_diff(self):
        var_name = f"metric_{uuid.uuid4().hex[:6]}"
        val = random.randint(1, 10000)
        diff_data = f" random text before \n + {var_name} = {val} \n some other text "

        metrics = self.generator._extract_metrics_from_diff(diff_data)
        self.assertIn(var_name, metrics)
        self.assertEqual(metrics[var_name], val)

    def test_extract_metrics_from_diff_multiple(self):
        var1 = f"m1_{uuid.uuid4().hex[:4]}"
        val1 = random.randint(1, 500)
        var2 = f"m2_{uuid.uuid4().hex[:4]}"
        val2 = random.randint(501, 1000)

        diff_data = f"diff line\n+{var1}={val1}\n {var2} = {val2}\n"
        metrics = self.generator._extract_metrics_from_diff(diff_data)

        self.assertEqual(metrics.get(var1), val1)
        self.assertEqual(metrics.get(var2), val2)