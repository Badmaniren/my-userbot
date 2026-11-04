import os
import shutil
import tempfile
import unittest
import uuid
import random
import io
from unittest.mock import patch, MagicMock
from skills.repo_release_exporter import RepoReleaseExporter


class TestRepoReleaseExporter(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.exporter = RepoReleaseExporter(self.repo_path)
        self.random_tag = f"v{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.random_stream_data = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_init_sets_attributes(self):
        self.assertEqual(self.exporter.repo_path, self.repo_path)
        self.assertIsNotNone(self.exporter.tagger)
        self.assertIsNotNone(self.exporter.pipeline)

    def test_export_release_pipeline_fails(self):
        with patch.object(self.exporter.pipeline, 'run_pipeline', return_value=False) as mock_pipeline:
            result = self.exporter.export_release(tag=self.random_tag)
            self.assertFalse(result)
            mock_pipeline.assert_called_once()

    def test_export_release_success_returns_archive_path(self):
        dummy_file_name = f"{uuid.uuid4().hex}.txt"
        dummy_file_path = os.path.join(self.repo_path, dummy_file_name)
        with open(dummy_file_path, 'w') as f:
            f.write(uuid.uuid4().hex)

        with patch.object(self.exporter.pipeline, 'run_pipeline', return_value=True), \
             patch.object(self.exporter.tagger, 'apply_and_push_tag') as mock_push_tag:

            archive_path = self.exporter.export_release(tag=self.random_tag)
            
            self.assertTrue(os.path.exists(archive_path))
            self.assertTrue(archive_path.endswith('.zip'))
            mock_push_tag.assert_called_once_with(self.random_tag)

    def test_export_release_with_default_tag(self):
        dummy_file_name = f"{uuid.uuid4().hex}.txt"
        dummy_file_path = os.path.join(self.repo_path, dummy_file_name)
        with open(dummy_file_path, 'w') as f:
            f.write(uuid.uuid4().hex)

        with patch.object(self.exporter.pipeline, 'run_pipeline', return_value=True), \
             patch.object(self.exporter.tagger, 'determine_next_version', return_value=self.random_tag) as mock_det_ver, \
             patch.object(self.exporter.tagger, 'apply_and_push_tag') as mock_push_tag:

            archive_path = self.exporter.export_release(tag=None)
            
            self.assertTrue(os.path.exists(archive_path))
            mock_det_ver.assert_called_once()
            mock_push_tag.assert_called_once_with(self.random_tag)

    def test_export_release_with_dest_path_success(self):
        dummy_file_name = f"{uuid.uuid4().hex}.txt"
        dummy_file_path = os.path.join(self.repo_path, dummy_file_name)
        expected_content = uuid.uuid4().hex
        with open(dummy_file_path, 'w') as f:
            f.write(expected_content)

        dest_folder = os.path.join(self.test_dir, f"dest_{uuid.uuid4().hex}")

        with patch.object(self.exporter.pipeline, 'run_pipeline', return_value=True), \
             patch.object(self.exporter.tagger, 'apply_and_push_tag'):

            result = self.exporter.export_release(tag=self.random_tag, dest_path=dest_folder)
            
            self.assertTrue(result)
            self.assertTrue(os.path.exists(dest_folder))
            extracted_file_path = os.path.join(dest_folder, dummy_file_name)
            self.assertTrue(os.path.exists(extracted_file_path))
            with open(extracted_file_path, 'r') as f:
                content = f.read()
            self.assertEqual(content, expected_content)

    def test_export_release_with_dest_path_missing_archive_fails(self):
        dest_folder = os.path.join(self.test_dir, f"dest_{uuid.uuid4().hex}")

        with patch.object(self.exporter.pipeline, 'run_pipeline', return_value=True), \
             patch.object(self.exporter.tagger, 'apply_and_push_tag'), \
             patch.object(self.exporter, '_package_artifacts', return_value=os.path.join(self.test_dir, f"{uuid.uuid4().hex}.zip")):

            result = self.exporter.export_release(tag=self.random_tag, dest_path=dest_folder)
            self.assertFalse(result)

    def test_batch_export_from_stream(self):
        stream = io.BytesIO(self.random_stream_data)
        expected_result = f"audit_result_{uuid.uuid4().hex}"

        with patch.object(self.exporter.pipeline, 'process_audit_stream', return_value=expected_result) as mock_process:
            res = self.exporter.batch_export_from_stream(stream)
            self.assertEqual(res, expected_result)
            mock_process.assert_called_once_with(stream)

    def test_package_artifacts_creates_zip_and_skips_git(self):
        git_dir = os.path.join(self.repo_path, '.git')
        os.makedirs(git_dir, exist_ok=True)
        git_file_path = os.path.join(git_dir, f"{uuid.uuid4().hex}.txt")
        with open(git_file_path, 'w') as f:
            f.write(uuid.uuid4().hex)

        valid_file_name = f"{uuid.uuid4().hex}.py"
        valid_file_path = os.path.join(self.repo_path, valid_file_name)
        with open(valid_file_path, 'w') as f:
            f.write(uuid.uuid4().hex)

        tag_with_slash = f"feature/{uuid.uuid4().hex}"
        archive_path = self.exporter._package_artifacts(tag_with_slash)

        self.assertTrue(os.path.exists(archive_path))
        import zipfile
        with zipfile.ZipFile(archive_path, 'r') as zf:
            namelist = zf.namelist()
            self.assertIn(valid_file_name, namelist)
            for name in namelist:
                self.assertFalse('.git' in name)