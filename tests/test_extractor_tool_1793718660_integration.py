import os
import shutil
import tempfile
import unittest
import uuid
import random

from skills.git_committer import GitCommitter
from skills.repo_monitor import RepoMonitor
from skills.repo_summarizer import RepoSummarizer
from skills.extractor_tool_1793718660 import MetadataExtractor


class TestMetadataExtractorIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.random_id = str(uuid.uuid4())
        self.random_key = f"key_{uuid.uuid4().hex[:8]}"
        self.random_val = f"val_{uuid.uuid4().hex[:8]}"
        self.extractor = MetadataExtractor()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_extract_from_text_random_data(self):
        unique_author = f"author_{uuid.uuid4()}"
        unique_title = f"title_{uuid.uuid4()}"

        markup_text = f"""---
title: {unique_title}
author: {unique_author}
{self.random_key}: {self.random_val}
---
# Header
Some content body with random token {self.random_id}
"""
        result = self.extractor.extract_from_text(markup_text)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("title"), unique_title)
        self.assertEqual(result.get("author"), unique_author)
        self.assertEqual(result.get(self.random_key), self.random_val)

    def test_extract_from_file_real_io(self):
        unique_tag = f"tag_{uuid.uuid4().hex}"
        unique_val = f"val_{uuid.uuid4().hex}"
        file_path = os.path.join(self.temp_dir, f"doc_{uuid.uuid4().hex[:6]}.md")

        markup_content = f"""<!--
meta_tag: {unique_tag}
meta_val: {unique_val}
-->
<content>Test document content {self.random_id}</content>
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markup_content)

        self.assertTrue(os.path.exists(file_path))
        extracted = self.extractor.extract_from_file(file_path)

        self.assertIsInstance(extracted, dict)
        self.assertEqual(extracted.get("meta_tag"), unique_tag)
        self.assertEqual(extracted.get("meta_val"), unique_val)

    def test_repo_integration_flow(self):
        repo_dir = os.path.join(self.temp_dir, f"repo_{uuid.uuid4().hex[:6]}")
        os.makedirs(repo_dir, exist_ok=True)

        committer = GitCommitter(repo_dir)
        monitor = RepoMonitor(repo_dir)
        summarizer = RepoSummarizer(repo_dir)

        test_filename = f"spec_{uuid.uuid4().hex[:8]}.markdown"
        full_path = os.path.join(repo_dir, test_filename)

        rand_version = f"v{random.randint(1, 100)}.{random.randint(0, 9)}"
        rand_status = f"status_{uuid.uuid4().hex[:6]}"

        content = f"""---
version: {rand_version}
status: {rand_status}
id: {self.random_id}
---
Repository specification content.
"""
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        commit_result = committer.commit_changes(full_path, f"Add specification {self.random_id}")
        self.assertIsInstance(commit_result, bool)

        status = monitor.check_status()
        self.assertIsInstance(status, str)

        extracted = self.extractor.extract_from_file(full_path)
        self.assertEqual(extracted.get("version"), rand_version)
        self.assertEqual(extracted.get("status"), rand_status)
        self.assertEqual(extracted.get("id"), self.random_id)

        summary = summarizer.generate_summary()
        self.assertIsInstance(summary, str)


if __name__ == "__main__":
    unittest.main()