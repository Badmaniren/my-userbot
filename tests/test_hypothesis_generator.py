import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.hypothesis_generator import HypothesisGenerator, HypothesisGeneratorError

class TestHypothesisGenerator(unittest.TestCase):
    def setUp(self):
        self.repo_path_val = f"/repo/{uuid.uuid4().hex}"
        self.mock_git_inspector = MagicMock()
        self.mock_lesson_parser = MagicMock()
        self.generator = HypothesisGenerator(
            git_inspector=self.mock_git_inspector,
            lesson_parser=self.mock_lesson_parser
        )

    def test_generate_hypotheses_success(self):
        random_commit = uuid.uuid4().hex
        random_author = "".join(random.choices(string.ascii_letters, k=8))
        random_message = f"fix bug {uuid.uuid4().hex}"
        
        commit_history_data = [
            {"hash": random_commit, "author": random_author, "message": random_message}
        ]
        self.mock_git_inspector.get_commit_history.return_value = commit_history_data

        random_lesson_id = uuid.uuid4().hex
        random_lesson_topic = "".join(random.choices(string.ascii_lowercase, k=10))
        lessons_data = [
            {"id": random_lesson_id, "topic": random_lesson_topic, "insights": [random_message]}
        ]
        self.mock_lesson_parser.parse_lessons.return_value = lessons_data

        with patch("skills.hypothesis_generator.open", create=True) as mock_open:
            mock_file = mock_open.return_value.__enter__.return_value
            mock_file.read.return_value = io.BytesIO(b"some random repo state stream").read()

            hypotheses = self.generator.generate_hypotheses(max_commits=random.randint(5, 50))

        self.assertIsInstance(hypotheses, list)
        self.assertTrue(len(hypotheses) > 0)
        
        found_match = False
        for hyp in hypotheses:
            self.assertIn("id", hyp)
            self.assertIn("description", hyp)
            self.assertIn("source", hyp)
            if random_message in hyp["description"] or random_lesson_topic in hyp["description"]:
                found_match = True

        self.assertTrue(found_match, "Generated hypotheses do not reflect input data from git history or lessons.")
        self.mock_git_inspector.get_commit_history.assert_called_once()
        self.mock_lesson_parser.parse_lessons.assert_called_once()

    def test_generate_hypotheses_inspector_failure(self):
        random_error_msg = f"Git failure {uuid.uuid4().hex}"
        self.mock_git_inspector.get_commit_history.side_effect = Exception(random_error_msg)

        with self.assertRaises(HypothesisGeneratorError) as ctx:
            self.generator.generate_hypotheses(max_commits=random.randint(1, 10))

        self.assertIn(random_error_msg, str(ctx.exception))

    def test_generate_hypotheses_parser_failure(self):
        self.mock_git_inspector.get_commit_history.return_value = [{"hash": uuid.uuid4().hex}]
        random_parser_error = f"Parser exploded {uuid.uuid4().hex}"
        self.mock_lesson_parser.parse_lessons.side_effect = Exception(random_parser_error)

        with self.assertRaises(HypothesisGeneratorError) as ctx:
            self.generator.generate_hypotheses(max_commits=random.randint(1, 10))

        self.assertIn(random_parser_error, str(ctx.exception))

    def test_prioritize_hypotheses(self):
        hyp_id_1 = uuid.uuid4().hex
        hyp_id_2 = uuid.uuid4().hex
        score_1 = random.randint(1, 100)
        score_2 = random.randint(1, 100)

        raw_hypotheses = [
            {"id": hyp_id_1, "description": f"Desc {uuid.uuid4().hex}", "score": score_1},
            {"id": hyp_id_2, "description": f"Desc {uuid.uuid4().hex}", "score": score_2}
        ]

        prioritized = self.generator.prioritize_hypotheses(raw_hypotheses)

        self.assertIsInstance(prioritized, list)
        self.assertEqual(len(prioritized), 2)
        
        if score_1 >= score_2:
            self.assertEqual(prioritized[0]["id"], hyp_id_1)
        else:
            self.assertEqual(prioritized[0]["id"], hyp_id_2)