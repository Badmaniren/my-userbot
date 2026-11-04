import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.repo_release_exporter import RepoReleaseExporter


class TestRepoReleaseExporter(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex[:8]}"

    def test_exporter_initialization_and_composition(self):
        rnd_path = f"/tmp/{uuid.uuid4().hex}"
        with patch('skills.repo_release_exporter.RepoTagger') as mock_tagger_cls, \
             patch('skills.repo_release_exporter.RepoCIPipeline') as mock_pipeline_cls:
            
            exporter = RepoReleaseExporter(rnd_path)
            
            mock_tagger_cls.assert_called_once_with(rnd_path)
            mock_pipeline_cls.assert_called_once_with(rnd_path)
            self.assertEqual(exporter.repo_path, rnd_path)

    def test_export_releases_success_flow(self):
        tag_name = f"v{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        export_dest = f"/exports/{uuid.uuid4().hex}.zip"

        with patch('skills.repo_release_exporter.RepoTagger') as mock_tagger_cls, \
             patch('skills.repo_release_exporter.RepoCIPipeline') as mock_pipeline_cls:
            
            mock_tagger = mock_tagger_cls.return_value
            mock_tagger.determine_next_version.return_value = tag_name
            mock_tagger.apply_and_push_tag.return_value = True

            mock_pipeline = mock_pipeline_cls.return_value
            mock_pipeline.run_pipeline.return_value = True

            exporter = RepoReleaseExporter(self.repo_path)
            
            with patch.object(exporter, '_package_artifacts', return_value=export_dest) as mock_package:
                result = exporter.export_release()
                
                mock_tagger.determine_next_version.assert_called_once()
                mock_pipeline.run_pipeline.assert_called_once()
                mock_tagger.apply_and_push_tag.assert_called_once_with(tag_name)
                mock_package.assert_called_once_with(tag_name)
                self.assertEqual(result, export_dest)

    def test_export_release_pipeline_fails(self):
        with patch('skills.repo_release_exporter.RepoTagger') as mock_tagger_cls, \
             patch('skills.repo_release_exporter.RepoCIPipeline') as mock_pipeline_cls:
            
            mock_tagger = mock_tagger_cls.return_value
            mock_tagger.determine_next_version.return_value = f"v{random.randint(1, 5)}.0.0"

            mock_pipeline = mock_pipeline_cls.return_value
            mock_pipeline.run_pipeline.return_value = False

            exporter = RepoReleaseExporter(self.repo_path)
            result = exporter.export_release()

            mock_pipeline.run_pipeline.assert_called_once()
            mock_tagger.apply_and_push_tag.assert_not_called()
            self.assertFalse(result)

    def test_batch_export_tags_with_stream(self):
        stream_data = ''.join(random.choices(string.ascii_letters + string.digits, k=64)).encode('utf-8')
        mock_stream = io.BytesIO(stream_data)

        with patch('skills.repo_release_exporter.RepoTagger') as mock_tagger_cls, \
             patch('skills.repo_release_exporter.RepoCIPipeline') as mock_pipeline_cls:
            
            mock_pipeline = mock_pipeline_cls.return_value
            mock_pipeline.process_audit_stream.return_value = True

            exporter = RepoReleaseExporter(self.repo_path)
            success = exporter.batch_export_from_stream(mock_stream)

            mock_pipeline.process_audit_stream.assert_called_once_with(mock_stream)
            self.assertTrue(success)

    def test_package_artifacts_internal_logic(self):
        target_tag = f"v{random.randint(10, 99)}.0.0"
        exporter = RepoReleaseExporter(self.repo_path)

        with patch('os.path.exists', return_value=True), \
             patch('zipfile.ZipFile') as mock_zipfile:
            
            res_path = exporter._package_artifacts(target_tag)
            self.assertIn(target_tag, res_path)
            mock_zipfile.assert_called_once()


if __name__ == '__main__':
    unittest.main()