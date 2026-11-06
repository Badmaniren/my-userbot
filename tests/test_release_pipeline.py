import unittest
from unittest.mock import patch
import uuid
import random
import io
import os

from skills.release_pipeline import ReleasePipeline


class TestReleasePipeline(unittest.TestCase):

    def test_release_pipeline_composition_and_execution(self):
        random_repo_path = f"/repo/{uuid.uuid4().hex}"
        random_output_path = f"/output/{uuid.uuid4().hex}.md"
        random_notes_content = uuid.uuid4().hex
        
        with patch("skills.release_pipeline.ReleaseNotesComposer") as mock_composer_cls, \
             patch("skills.release_pipeline.ReleaseNotesPublisher") as mock_publisher_cls:
            
            mock_composer_instance = mock_composer_cls.return_value
            mock_composer_instance.compose.return_value = random_notes_content
            
            mock_publisher_instance = mock_publisher_cls.return_value
            mock_publisher_instance.publish.return_value = True

            pipeline = ReleasePipeline(repo_path=random_repo_path)
            
            mock_composer_cls.assert_called_once_with(repo_path=random_repo_path)
            mock_publisher_cls.assert_called_once_with(repo_path=random_repo_path)

            result = pipeline.run(output_path=random_output_path)

            mock_composer_instance.compose.assert_called_once_with(output_path=random_output_path)
            mock_publisher_instance.publish.assert_called_once_with(output_path=random_output_path)
            
            self.assertTrue(result)

    def test_release_pipeline_publisher_failure(self):
        random_repo_path = f"/repo/{uuid.uuid4().hex}"
        random_output_path = f"/dist/{uuid.uuid4().hex}"
        random_notes_content = uuid.uuid4().hex
        
        with patch("skills.release_pipeline.ReleaseNotesComposer") as mock_composer_cls, \
             patch("skills.release_pipeline.ReleaseNotesPublisher") as mock_publisher_cls:
            
            mock_composer_instance = mock_composer_cls.return_value
            mock_composer_instance.compose.return_value = random_notes_content
            
            mock_publisher_instance = mock_publisher_cls.return_value
            mock_publisher_instance.publish.return_value = False

            pipeline = ReleasePipeline(repo_path=random_repo_path)
            result = pipeline.run(output_path=random_output_path)

            mock_composer_instance.compose.assert_called_once_with(output_path=random_output_path)
            mock_publisher_instance.publish.assert_called_once_with(output_path=random_output_path)
            
            self.assertFalse(result)

    def test_release_pipeline_with_stream_mocking(self):
        random_repo_path = f"/repo/{uuid.uuid4().hex}"
        random_output_path = f"/tmp/{uuid.uuid4().hex}"
        random_bytes_content = uuid.uuid4().hex.encode('utf-8')
        
        with patch("skills.release_pipeline.ReleaseNotesComposer") as mock_composer_cls, \
             patch("skills.release_pipeline.ReleaseNotesPublisher") as mock_publisher_cls:
            
            mock_composer_instance = mock_composer_cls.return_value
            
            def side_effect_compose(output_path):
                stream = io.BytesIO(random_bytes_content)
                return stream.read().decode('utf-8')

            mock_composer_instance.compose.side_effect = side_effect_compose
            
            mock_publisher_instance = mock_publisher_cls.return_value
            mock_publisher_instance.publish.return_value = True

            pipeline = ReleasePipeline(repo_path=random_repo_path)
            result = pipeline.run(output_path=random_output_path)

            self.assertTrue(result)
            mock_composer_instance.compose.assert_called_once_with(output_path=random_output_path)
            mock_publisher_instance.publish.assert_called_once_with(output_path=random_output_path)


if __name__ == "__main__":
    unittest.main()