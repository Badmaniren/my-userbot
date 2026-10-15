import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string

from skills.hypothesis_generator import HypothesisGenerator, HypothesisGeneratorError


class TestHypothesisGenerator(unittest.TestCase):

    def setUp(self):
        self.git_inspector_mock = MagicMock()
        self.lesson_parser_mock = MagicMock()
        self.generator = HypothesisGenerator(self.git_inspector_mock, self.lesson_parser_mock)

        self.random_title = f"lesson_{uuid.uuid4().hex}"
        self.random_content = "".join(random.choices(string.ascii_letters + string.digits, k=25))
        self.random_lesson_id = uuid.uuid4().hex
        self.random_commit = uuid.uuid4().hex

    def test_generate_hypotheses_success(self):
        lesson_data = [{
            "id": self.random_lesson_id,
            "title": self.random_title,
            "content": self.random_content,
            "commit": self.random_commit
        }]
        self.lesson_parser_mock.parse_lessons.return_value = lesson_data

        commit_history = [{"hash": self.random_commit, "message": uuid.uuid4().hex}]
        self.git_inspector_mock.get_commit_history.return_value = commit_history

        hypotheses = self.generator.generate_hypotheses()

        self.assertEqual(len(hypotheses), 1)
        self.assertEqual(hypotheses[0]["title"], self.random_title)
        self.assertEqual(hypotheses[0]["lesson_id"], self.random_lesson_id)
        self.assertEqual(hypotheses[0]["commit"], self.random_commit)
        self.assertIn(self.random_title, hypotheses[0]["description"])
        self.assertIn(str(len(self.random_content)), hypotheses[0]["description"])

        self.lesson_parser_mock.parse_lessons.assert_called_once()
        self.git_inspector_mock.get_commit_history.assert_called_once()

    def test_generate_alias_method(self):
        self.lesson_parser_mock.parse_lessons.return_value = []
        self.git_inspector_mock.get_commit_history.return_value = []

        result = self.generator.generate()
        self.assertIsInstance(result, list)

    def test_lesson_parser_error_handling(self):
        error_message = uuid.uuid4().hex
        self.lesson_parser_mock.parse_lessons.side_effect = Exception(error_message)

        with self.assertRaises(HypothesisGeneratorError) as ctx:
            self.generator.generate_hypotheses()

        self.assertIn(error_message, str(ctx.exception))

    def test_lesson_parser_custom_exception_handling(self):
        error_message = uuid.uuid4().hex

        class CustomLessonParserError(Exception):
            pass

        self.lesson_parser_mock.LessonParserError = CustomLessonParserError
        self.lesson_parser_mock.parse_lessons.side_effect = CustomLessonParserError(error_message)

        with self.assertRaises(HypothesisGeneratorError) as ctx:
            self.generator.generate_hypotheses()

        self.assertIn(error_message, str(ctx.exception))

    def test_git_inspector_error_handling(self):
        self.lesson_parser_mock.parse_lessons.return_value = []
        git_error_message = uuid.uuid4().hex
        self.git_inspector_mock.get_commit_history.side_effect = Exception(git_error_message)

        with self.assertRaises(HypothesisGeneratorError) as ctx:
            self.generator.generate_hypotheses()

        self.assertIn(git_error_message, str(ctx.exception))

    def test_analyze_repository_context(self):
        random_commit_hash = uuid.uuid4().hex
        random_file_path = f"src/{uuid.uuid4().hex}.py"
        random_diff = uuid.uuid4().hex
        random_file_content = uuid.uuid4().hex

        self.git_inspector_mock.get_file_diff.return_value = random_diff
        self.git_inspector_mock.read_file_at_commit.return_value = random_file_content

        context = self.generator._analyze_repository_context(random_commit_hash, random_file_path)

        self.assertEqual(context["diff"], random_diff)
        self.assertEqual(context["file_content"], random_file_content)
        self.git_inspector_mock.get_file_diff.assert_called_once_with(random_commit_hash, random_file_path)
        self.git_inspector_mock.read_file_at_commit.assert_called_once_with(random_commit_hash, random_file_path)


if __name__ == '__main__':
    unittest.main()