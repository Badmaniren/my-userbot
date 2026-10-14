import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import os

from skills.lesson_parser import LessonParser


class TestLessonParser(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/repo/{uuid.uuid4().hex}"
        self.parser = LessonParser(self.random_repo_path)

    def test_parse_success_and_failure_history(self):
        random_success_id = uuid.uuid4().hex
        random_fail_id = uuid.uuid4().hex
        random_commit_hash = uuid.uuid4().hex[:8]
        random_file_path = f"history/{uuid.uuid4().hex}.json"

        mock_history_data = [
            {"commit": random_commit_hash, "message": f"Fixed {random_success_id}"},
            {"commit": uuid.uuid4().hex[:8], "message": f"Broken by {random_fail_id}"}
        ]

        raw_file_content = (
            f'{{"success_id": "{random_success_id}", "status": "success"}}\n'
            f'{{"fail_id": "{random_fail_id}", "status": "failure"}}'
        ).encode('utf-8')

        with patch("skills.lesson_parser.GitInspector") as MockGitInspector:
            instance = MockGitInspector.return_value
            instance.get_commit_history.return_value = mock_history_data
            instance.read_file_at_commit.return_value = raw_file_content

            parsed_data = self.parser.parse_lesson_history(random_file_path)

            instance.get_commit_history.assert_called_once()
            instance.read_file_at_commit.assert_called_with(random_commit_hash, random_file_path)

            self.assertIsInstance(parsed_data, list)
            self.assertTrue(len(parsed_data) >= 2)

            found_success = any(item.get("success_id") == random_success_id for item in parsed_data)
            found_fail = any(item.get("fail_id") == random_fail_id for item in parsed_data)

            self.assertTrue(found_success, f"Парсер не нашел случайный success_id: {random_success_id}")
            self.assertTrue(found_fail, f"Парсер не нашел случайный fail_id: {random_fail_id}")

    def test_extract_error_patterns_chaos(self):
        random_error_word = ''.join(random.choices(string.ascii_lowercase, k=10))
        random_error_code = random.randint(1000, 9999)
        random_diff_content = f"- error: {random_error_word}\n+ fixed code {random_error_code}"

        random_commit = uuid.uuid4().hex

        with patch("skills.lesson_parser.GitInspector") as MockGitInspector:
            instance = MockGitInspector.return_value
            instance.get_latest_changes.return_value = [{"hash": random_commit}]
            instance.get_file_diff.return_value = random_diff_content

            patterns = self.parser.extract_error_patterns()

            self.assertIsInstance(patterns, dict)
            self.assertIn("patterns", patterns)

            flattened_patterns = str(patterns)
            self.assertIn(random_error_word, flattened_patterns)
            self.assertIn(str(random_error_code), flattened_patterns)

    def test_prepare_data_for_hypothesis_generator(self):
        random_pattern_name = f"pattern_{uuid.uuid4().hex[:6]}"
        random_frequency = random.randint(5, 50)

        mock_analysis_result = {
            random_pattern_name: {
                "frequency": random_frequency,
                "context": f"unga made a mistake with {uuid.uuid4().hex}"
            }
        }

        with patch("skills.lesson_parser.GitInspector") as MockGitInspector:
            instance = MockGitInspector.return_value
            instance.analyze_repository.return_value = mock_analysis_result

            prepared_dataset = self.parser.prepare_hypothesis_data()

            self.assertIsInstance(prepared_dataset, dict)
            self.assertIn("hypotheses_inputs", prepared_dataset)

            dataset_items = prepared_dataset["hypotheses_inputs"]
            matched_item = next((item for item in dataset_items if item.get("name") == random_pattern_name), None)

            self.assertIsNotNone(matched_item, f"Не найден сгенерированный паттерн {random_pattern_name}")
            self.assertEqual(matched_item["frequency"], random_frequency)


if __name__ == "__main__":
    unittest.main()