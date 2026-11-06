import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.release_pipeline import ReleasePipeline


class TestReleasePipeline(unittest.TestCase):

    def test_release_pipeline_initialization_and_run(self):
        rand_repo = f"/tmp/{uuid.uuid4().hex}/{''.join(random.choices(string.ascii_lowercase, k=6))}"
        rand_output = f"/var/releases/{uuid.uuid4().hex}.md"
        expected_publish_result = random.choice([True, False, "success", ""])

        with patch("skills.release_pipeline.ReleaseNotesComposer") as MockComposer, \
             patch("skills.release_pipeline.ReleaseNotesPublisher") as MockPublisher:

            mock_composer_instance = MockComposer.return_value
            mock_publisher_instance = MockPublisher.return_value
            mock_publisher_instance.publish.return_value = expected_publish_result

            pipeline = ReleasePipeline(repo_path=rand_repo)

            MockComposer.assert_called_once_with(repo_path=rand_repo)
            MockPublisher.assert_called_once_with(repo_path=rand_repo)
            self.assertEqual(pipeline.repo_path, rand_repo)

            run_result = pipeline.run(output_path=rand_output)

            mock_composer_instance.compose.assert_called_once_with(output_path=rand_output)
            mock_publisher_instance.publish.assert_called_once_with(output_path=rand_output)
            self.assertEqual(run_result, bool(expected_publish_result))

    def test_release_pipeline_run_handles_truthy_falsy_publishing(self):
        rand_repo = f"repo_{uuid.uuid4().hex}"
        rand_output = f"output_{uuid.uuid4().hex}"

        for truthy_val in [True, 1, "non_empty", ["item"]]:
            with patch("skills.release_pipeline.ReleaseNotesComposer"), \
                 patch("skills.release_pipeline.ReleaseNotesPublisher") as MockPublisher:

                MockPublisher.return_value.publish.return_value = truthy_val
                pipeline = ReleasePipeline(repo_path=rand_repo)
                self.assertTrue(pipeline.run(output_path=rand_output))

        for falsy_val in [False, 0, "", None]:
            with patch("skills.release_pipeline.ReleaseNotesComposer"), \
                 patch("skills.release_pipeline.ReleaseNotesPublisher") as MockPublisher:

                MockPublisher.return_value.publish.return_value = falsy_val
                pipeline = ReleasePipeline(repo_path=rand_repo)
                self.assertFalse(pipeline.run(output_path=rand_output))


if __name__ == "__main__":
    unittest.main()