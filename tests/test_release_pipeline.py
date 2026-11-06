import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.release_pipeline import ReleasePipeline

class TestReleasePipeline(unittest.TestCase):
    def setUp(self):
        self.random_repo_path = f"/repo/{uuid.uuid4().hex}/{''.join(random.choices(string.ascii_lowercase, k=6))}"
        self.random_output_path = f"/output/{uuid.uuid4().hex}/{''.join(random.choices(string.ascii_lowercase, k=6))}.md"

    @patch('skills.release_pipeline.ReleaseNotesPublisher')
    @patch('skills.release_pipeline.ReleaseNotesComposer')
    def test_release_pipeline_run_success(self, mock_composer_cls, mock_publisher_cls):
        mock_composer_instance = mock_composer_cls.return_value
        mock_publisher_instance = mock_publisher_cls.return_value

        expected_publish_result = random.choice([True, 1, "success_token_" + uuid.uuid4().hex])
        mock_publisher_instance.publish.return_value = expected_publish_result

        pipeline = ReleasePipeline(repo_path=self.random_repo_path)
        
        self.assertEqual(pipeline.repo_path, self.random_repo_path)
        self.assertEqual(pipeline.composer, mock_composer_instance)
        self.assertEqual(pipeline.publisher, mock_publisher_instance)

        result = pipeline.run(output_path=self.random_output_path)

        mock_composer_instance.compose.assert_called_once_with(output_path=self.random_output_path)
        mock_publisher_instance.publish.assert_called_once_with(output_path=self.random_output_path)
        self.assertTrue(result)

    @patch('skills.release_pipeline.ReleaseNotesPublisher')
    @patch('skills.release_pipeline.ReleaseNotesComposer')
    def test_release_pipeline_run_failure(self, mock_composer_cls, mock_publisher_cls):
        mock_composer_instance = mock_composer_cls.return_value
        mock_publisher_instance = mock_publisher_cls.return_value

        expected_publish_result = random.choice([False, 0, None, ""])
        mock_publisher_instance.publish.return_value = expected_publish_result

        pipeline = ReleasePipeline(repo_path=self.random_repo_path)
        result = pipeline.run(output_path=self.random_output_path)

        mock_composer_instance.compose.assert_called_once_with(output_path=self.random_output_path)
        mock_publisher_instance.publish.assert_called_once_with(output_path=self.random_output_path)
        self.assertFalse(result)

    @patch('skills.release_pipeline.ReleaseNotesPublisher')
    @patch('skills.release_pipeline.ReleaseNotesComposer')
    def test_release_pipeline_initialization_passes_repo_path(self, mock_composer_cls, mock_publisher_cls):
        ReleasePipeline(repo_path=self.random_repo_path)

        mock_composer_cls.assert_called_once_with(repo_path=self.random_repo_path)
        mock_publisher_cls.assert_called_once_with(repo_path=self.random_repo_path)

if __name__ == '__main__':
    unittest.main()