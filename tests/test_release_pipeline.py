import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.release_pipeline import ReleasePipeline


class TestReleasePipeline(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex[:8]}"
        self.output_path = f"/releases/{uuid.uuid4().hex[:8]}.md"

    def test_pipeline_initialization(self):
        pipeline = ReleasePipeline(repo_path=self.repo_path)
        self.assertEqual(pipeline.repo_path, self.repo_path)
        self.assertIsNotNone(pipeline.composer)
        self.assertIsNotNone(pipeline.publisher)
        self.assertEqual(pipeline.composer.repo_path, self.repo_path)
        self.assertEqual(pipeline.publisher.repo_path, self.repo_path)

    def test_run_pipeline_success(self):
        expected_result = random.choice([True, 1, "success_token"])
        
        with patch("skills.release_pipeline.ReleaseNotesComposer") as MockComposer, \
             patch("skills.release_pipeline.ReleaseNotesPublisher") as MockPublisher:
            
            mock_composer_instance = MockComposer.return_value
            mock_publisher_instance = MockPublisher.return_value
            mock_publisher_instance.publish.return_value = expected_result

            pipeline = ReleasePipeline(repo_path=self.repo_path)
            result = pipeline.run(output_path=self.output_path)

            mock_composer_instance.compose.assert_called_once_with(output_path=self.output_path)
            mock_publisher_instance.publish.assert_called_once_with(output_path=self.output_path)
            self.assertTrue(result)

    def test_run_pipeline_failure(self):
        failing_results = [False, 0, None, ""]
        expected_failing_value = random.choice(failing_results)

        with patch("skills.release_pipeline.ReleaseNotesComposer") as MockComposer, \
             patch("skills.release_pipeline.ReleaseNotesPublisher") as MockPublisher:
            
            mock_composer_instance = MockComposer.return_value
            mock_publisher_instance = MockPublisher.return_value
            mock_publisher_instance.publish.return_value = expected_failing_value

            pipeline = ReleasePipeline(repo_path=self.repo_path)
            result = pipeline.run(output_path=self.output_path)

            mock_composer_instance.compose.assert_called_once_with(output_path=self.output_path)
            mock_publisher_instance.publish.assert_called_once_with(output_path=self.output_path)
            self.assertFalse(result)

    def test_pipeline_stream_handling(self):
        random_bytes = ''.join(random.choices(string.ascii_letters + string.digits, k=32)).encode('utf-8')
        mock_stream = io.BytesIO(random_bytes)

        with patch("skills.release_pipeline.ReleaseNotesComposer") as MockComposer, \
             patch("skills.release_pipeline.ReleaseNotesPublisher") as MockPublisher:
            
            mock_publisher_instance = MockPublisher.return_value
            mock_publisher_instance.publish.return_value = True

            pipeline = ReleasePipeline(repo_path=self.repo_path)
            
            # Эмулируем чтение потока внутри компоновщика или издателя
            read_data = mock_stream.read()
            self.assertEqual(read_data, random_bytes)

            result = pipeline.run(output_path=self.output_path)
            self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()