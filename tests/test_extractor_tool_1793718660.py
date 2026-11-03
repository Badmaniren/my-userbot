import io
import os
import random
import string
import sys
import unittest
import uuid
from unittest.mock import MagicMock, patch

import skills.extractor_tool_1793718660 as target_module


def rand_str(length=10):
    return f"{uuid.uuid4().hex[:length]}_{''.join(random.choices(string.ascii_letters, k=4))}"


class TestExtractorTool1793718660(unittest.TestCase):

    def setUp(self):
        self.test_id = rand_str(8)

    def test_extract_meta_tags_dynamic(self):
        meta_name = f"author_{rand_str(6)}"
        meta_value = f"user_{rand_str(10)}"
        markup = f"<html><head><meta name='{meta_name}' content='{meta_value}'></head></html>"

        if hasattr(target_module, "MetadataExtractor"):
            extractor = target_module.MetadataExtractor(markup)
            res = extractor.extract_meta() if hasattr(extractor, "extract_meta") else extractor.extract()
        elif hasattr(target_module, "extract_metadata"):
            res = target_module.extract_metadata(markup)
        elif hasattr(target_module, "extract_meta_tags"):
            res = target_module.extract_meta_tags(markup)
        else:
            res = target_module.parse(markup)

        self.assertIsInstance(res, dict)
        self.assertIn(meta_name, res)
        self.assertEqual(res[meta_name], meta_value)

    def test_extract_og_property_tags(self):
        og_prop = f"og:{rand_str(5)}"
        og_content = f"content_{rand_str(12)}"
        markup = f"<!DOCTYPE html><html><head><meta property='{og_prop}' content='{og_content}'/></head><body></body></html>"

        if hasattr(target_module, "MetadataExtractor"):
            extractor = target_module.MetadataExtractor(markup)
            res = extractor.extract_meta() if hasattr(extractor, "extract_meta") else extractor.extract()
        elif hasattr(target_module, "extract_metadata"):
            res = target_module.extract_metadata(markup)
        else:
            res = target_module.extract_meta_tags(markup)

        self.assertIn(og_prop, res)
        self.assertEqual(res[og_prop], og_content)

    def test_extract_title_tag(self):
        expected_title = f"Page_{rand_str(14)}"
        markup = f"<html><head><title>{expected_title}</title></head></html>"

        if hasattr(target_module, "MetadataExtractor"):
            extractor = target_module.MetadataExtractor(markup)
            if hasattr(extractor, "extract_title"):
                title = extractor.extract_title()
            else:
                res = extractor.extract()
                title = res.get("title")
        elif hasattr(target_module, "extract_title"):
            title = target_module.extract_title(markup)
        else:
            res = target_module.extract_metadata(markup)
            title = res.get("title")

        self.assertEqual(title, expected_title)

    def test_multiple_random_meta_pairs(self):
        num_pairs = random.randint(3, 8)
        expected_dict = {
            f"key_{rand_str(4)}_{i}": f"val_{rand_str(8)}_{i}"
            for i in range(num_pairs)
        }
        meta_html = "".join(
            [f"<meta name='{k}' content='{v}'>" for k, v in expected_dict.items()]
        )
        markup = f"<html><head>{meta_html}</head></html>"

        if hasattr(target_module, "MetadataExtractor"):
            extractor = target_module.MetadataExtractor(markup)
            res = extractor.extract_meta() if hasattr(extractor, "extract_meta") else extractor.extract()
        else:
            res = target_module.extract_metadata(markup)

        for k, v in expected_dict.items():
            self.assertIn(k, res)
            self.assertEqual(res[k], v)

    def test_empty_and_malformed_markup(self):
        invalid_markup = f"<{rand_str(5)}>unclosed_{rand_str(8)}"

        if hasattr(target_module, "MetadataExtractor"):
            extractor = target_module.MetadataExtractor(invalid_markup)
            res = extractor.extract_meta() if hasattr(extractor, "extract_meta") else extractor.extract()
        else:
            res = target_module.extract_metadata(invalid_markup)

        self.assertIsInstance(res, dict)

    def test_stream_reading_and_extraction(self):
        rand_key = f"stream_key_{rand_str(6)}"
        rand_val = f"stream_val_{rand_str(10)}"
        raw_html = f"<html><head><meta name='{rand_key}' content='{rand_val}'/></head></html>".encode("utf-8")

        bytes_io = io.BytesIO(raw_html)

        with patch("builtins.open", return_value=bytes_io):
            dummy_path = f"/tmp/{rand_str(8)}.html"
            if hasattr(target_module, "extract_from_file"):
                res = target_module.extract_from_file(dummy_path)
                self.assertEqual(res.get(rand_key), rand_val)
            elif hasattr(target_module, "MetadataExtractor") and hasattr(target_module.MetadataExtractor, "from_file"):
                extractor = target_module.MetadataExtractor.from_file(dummy_path)
                res = extractor.extract()
                self.assertEqual(res.get(rand_key), rand_val)

    def test_git_committer_if_present(self):
        if hasattr(target_module, "GitCommitter"):
            repo_path = f"/tmp/repo_{rand_str(6)}"
            commit_msg = f"Commit {rand_str(10)}"

            committer = target_module.GitCommitter(repo_path)
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                if hasattr(committer, "commit"):
                    res = committer.commit(commit_msg)
                    self.assertIsInstance(res, bool)

    def test_repo_monitor_if_present(self):
        if hasattr(target_module, "RepoMonitor"):
            repo_path = f"/tmp/repo_{rand_str(6)}"
            monitor = target_module.RepoMonitor(repo_path)
            with patch("os.path.exists", return_value=True):
                if hasattr(monitor, "check_status"):
                    status = monitor.check_status()
                    self.assertIsInstance(status, str)


if __name__ == "__main__":
    unittest.main()