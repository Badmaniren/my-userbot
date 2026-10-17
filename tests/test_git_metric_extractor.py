import unittest
import uuid
import random
import string
import io
from unittest.mock import MagicMock, patch

from skills.git_metric_extractor import (
    GitMetricExtractor,
    GitMetricExtractorError,
)


def _rnd_str(prefix="test_", length=8):
    chars = string.ascii_lowercase + string.digits
    suffix = "".join(random.choices(chars, k=length))
    return f"{prefix}{uuid.uuid4().hex[:6]}_{suffix}"


def _rnd_hex(length=40):
    chars = string.hexdigits.lower()
    return "".join(random.choices(chars, k=length))


def _generate_numstat_line(file_path=None, binary=False):
    if file_path is None:
        file_path = f"{_rnd_str('src/')}/{_rnd_str('mod')}.py"
    if binary:
        return f"-\t-\t{file_path}", 0, 0, file_path
    adds = random.randint(1, 200)
    dels = random.randint(1, 200)
    return f"{adds}\t{dels}\t{file_path}", adds, dels, file_path


class TestGitMetricExtractor(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/{_rnd_str('repo_root')}/{_rnd_str('sub')}"

    def test_init_success_with_valid_repo_path(self):
        inspector_mock = MagicMock()
        with patch("skills.git_metric_extractor.GitInspector", return_value=inspector_mock) as mock_cls:
            extractor = GitMetricExtractor(repo_path=self.random_repo_path)
            self.assertEqual(extractor.repo_path, self.random_repo_path)
            mock_cls.assert_called_once_with(self.random_repo_path)
            self.assertIs(extractor.inspector, inspector_mock)

    def test_init_raises_error_on_invalid_repo_path(self):
        invalid_paths = ["", None, 12345, []]
        for bad_path in invalid_paths:
            with self.assertRaises(GitMetricExtractorError):
                GitMetricExtractor(repo_path=bad_path)

    def test_parse_diff_stat_random_numeric_and_binary_entries(self):
        extractor = GitMetricExtractor(repo_path=self.random_repo_path, inspector=MagicMock())

        count = random.randint(3, 7)
        lines = []
        expected_adds = 0
        expected_dels = 0
        expected_files = []

        for _ in range(count):
            line, adds, dels, file_name = _generate_numstat_line()
            lines.append(line)
            expected_adds += adds
            expected_dels += dels
            expected_files.append(file_name)

        binary_line, _, _, bin_file = _generate_numstat_line(binary=True)
        lines.append(binary_line)
        expected_files.append(bin_file)

        raw_numstat = "\n".join(lines) + "\n"

        result = extractor.parse_diff_stat(raw_numstat)

        self.assertEqual(result["additions"], expected_adds)
        self.assertEqual(result["deletions"], expected_dels)
        self.assertEqual(result["total_churn"], expected_adds + expected_dels)
        self.assertEqual(result["files_changed"], expected_files)
        self.assertEqual(len(result["files_changed"]), count + 1)

    def test_parse_diff_stat_empty_or_whitespace_diff(self):
        extractor = GitMetricExtractor(repo_path=self.random_repo_path, inspector=MagicMock())
        empty_inputs = ["", "   \n\t  \n  ", "\n\n"]
        for empty_text in empty_inputs:
            result = extractor.parse_diff_stat(empty_text)
            self.assertEqual(result["additions"], 0)
            self.assertEqual(result["deletions"], 0)
            self.assertEqual(result["total_churn"], 0)
            self.assertEqual(result["files_changed"], [])

    def test_extract_commit_metrics_success(self):
        mock_inspector = MagicMock()
        commit_hash = _rnd_hex(40)
        line, adds, dels, filename = _generate_numstat_line()
        mock_inspector.get_file_diff.return_value = line

        extractor = GitMetricExtractor(repo_path=self.random_repo_path, inspector=mock_inspector)
        metrics = extractor.extract_commit_metrics(commit_hash)

        mock_inspector.get_file_diff.assert_called_once_with(commit_hash)
        self.assertEqual(metrics["commit_hash"], commit_hash)
        self.assertEqual(metrics["additions"], adds)
        self.assertEqual(metrics["deletions"], dels)
        self.assertEqual(metrics["total_churn"], adds + dels)
        self.assertIn(filename, metrics["files_changed"])

    def test_extract_commit_metrics_invalid_hash(self):
        extractor = GitMetricExtractor(repo_path=self.random_repo_path, inspector=MagicMock())
        with self.assertRaises(GitMetricExtractorError):
            extractor.extract_commit_metrics("")

        with self.assertRaises(GitMetricExtractorError):
            extractor.extract_commit_metrics(None)

    def test_extract_commit_metrics_inspector_failure(self):
        mock_inspector = MagicMock()
        commit_hash = _rnd_hex(40)
        err_msg = _rnd_str("git_fail_")
        mock_inspector.get_file_diff.side_effect = RuntimeError(err_msg)

        extractor = GitMetricExtractor(repo_path=self.random_repo_path, inspector=mock_inspector)
        with self.assertRaises(GitMetricExtractorError) as ctx:
            extractor.extract_commit_metrics(commit_hash)
        self.assertIn(err_msg, str(ctx.exception))

    def test_calculate_churn_rate_computations(self):
        extractor = GitMetricExtractor(repo_path=self.random_repo_path, inspector=MagicMock())

        total_churn = random.randint(100, 5000)
        total_commits = random.randint(2, 50)
        expected_rate = round(float(total_churn) / total_commits, 4)

        rate = extractor.calculate_churn_rate(total_churn, total_commits)
        self.assertAlmostEqual(rate, expected_rate, places=4)

        zero_commit_rate = extractor.calculate_churn_rate(total_churn, 0)
        self.assertEqual(zero_commit_rate, 0.0)

        zero_churn_rate = extractor.calculate_churn_rate(0, total_commits)
        self.assertEqual(zero_churn_rate, 0.0)

    def test_calculate_churn_rate_negative_values_raise_error(self):
        extractor = GitMetricExtractor(repo_path=self.random_repo_path, inspector=MagicMock())
        with self.assertRaises(GitMetricExtractorError):
            extractor.calculate_churn_rate(-random.randint(1, 100), random.randint(1, 10))
        with self.assertRaises(GitMetricExtractorError):
            extractor.calculate_churn_rate(random.randint(1, 100), -random.randint(1, 10))

    def test_extract_history_metrics_aggregation(self):
        mock_inspector = MagicMock()
        num_commits = random.randint(3, 6)
        commits_data = []
        expected_total_additions = 0
        expected_total_deletions = 0
        expected_file_frequency = {}

        shared_filename = f"core/{_rnd_str('common')}.py"

        for _ in range(num_commits):
            c_hash = _rnd_hex(40)
            c_file = f"src/{_rnd_str('file')}.py"
            adds_1 = random.randint(10, 50)
            dels_1 = random.randint(5, 30)
            adds_2 = random.randint(1, 10)
            dels_2 = random.randint(1, 5)

            diff_text = f"{adds_1}\t{dels_1}\t{c_file}\n{adds_2}\t{dels_2}\t{shared_filename}\n"
            commits_data.append({"hash": c_hash, "diff": diff_text})

            expected_total_additions += (adds_1 + adds_2)
            expected_total_deletions += (dels_1 + dels_2)
            expected_file_frequency[c_file] = expected_file_frequency.get(c_file, 0) + 1
            expected_file_frequency[shared_filename] = expected_file_frequency.get(shared_filename, 0) + 1

        mock_inspector.get_commit_history.return_value = [c["hash"] for c in commits_data]

        def get_diff_side_effect(chash):
            for c in commits_data:
                if c["hash"] == chash:
                    return c["diff"]
            return ""

        mock_inspector.get_file_diff.side_effect = get_diff_side_effect

        extractor = GitMetricExtractor(repo_path=self.random_repo_path, inspector=mock_inspector)
        summary = extractor.extract_history_metrics(max_count=num_commits)

        mock_inspector.get_commit_history.assert_called_once_with(num_commits)
        self.assertEqual(summary["commits_analyzed"], num_commits)
        self.assertEqual(summary["total_additions"], expected_total_additions)
        self.assertEqual(summary["total_deletions"], expected_total_deletions)
        expected_churn = expected_total_additions + expected_total_deletions
        self.assertEqual(summary["total_churn"], expected_churn)

        expected_churn_rate = round(float(expected_churn) / num_commits, 4)
        self.assertAlmostEqual(summary["churn_rate"], expected_churn_rate, places=4)

        self.assertEqual(summary["file_frequencies"][shared_filename], num_commits)
        self.assertEqual(len(summary["modified_files"]), len(expected_file_frequency))

    def test_extract_history_metrics_empty_repo(self):
        mock_inspector = MagicMock()
        mock_inspector.get_commit_history.return_value = []

        extractor = GitMetricExtractor(repo_path=self.random_repo_path, inspector=mock_inspector)
        max_limit = random.randint(5, 20)
        summary = extractor.extract_history_metrics(max_count=max_limit)

        mock_inspector.get_commit_history.assert_called_once_with(max_limit)
        self.assertEqual(summary["commits_analyzed"], 0)
        self.assertEqual(summary["total_additions"], 0)
        self.assertEqual(summary["total_deletions"], 0)
        self.assertEqual(summary["total_churn"], 0)
        self.assertEqual(summary["churn_rate"], 0.0)
        self.assertEqual(summary["modified_files"], [])
        self.assertEqual(summary["file_frequencies"], {})

    def test_extract_history_metrics_inspector_exception_wrapped(self):
        mock_inspector = MagicMock()
        err_rand = _rnd_str("git_history_crash_")
        mock_inspector.get_commit_history.side_effect = Exception(err_rand)

        extractor = GitMetricExtractor(repo_path=self.random_repo_path, inspector=mock_inspector)
        with self.assertRaises(GitMetricExtractorError) as ctx:
            extractor.extract_history_metrics(max_count=random.randint(1, 10))
        self.assertIn(err_rand, str(ctx.exception))

    def test_extract_file_churn_ranking(self):
        extractor = GitMetricExtractor(repo_path=self.random_repo_path, inspector=MagicMock())
        f1 = f"src/{_rnd_str('hotspot')}.py"
        f2 = f"src/{_rnd_str('regular')}.py"
        f3 = f"src/{_rnd_str('stable')}.py"

        count1 = random.randint(15, 20)
        count2 = random.randint(8, 14)
        count3 = random.randint(1, 5)

        file_frequencies = {f2: count2, f1: count1, f3: count3}

        ranked = extractor.get_hotspot_files(file_frequencies, top_n=2)

        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0], (f1, count1))
        self.assertEqual(ranked[1], (f2, count2))

    def test_stream_diff_parsing_with_bytes_io(self):
        mock_inspector = MagicMock()
        random_file = f"pkg/{_rnd_str('stream')}.py"
        adds = random.randint(5, 50)
        dels = random.randint(2, 20)
        raw_bytes = f"{adds}\t{dels}\t{random_file}\n".encode("utf-8")

        mock_stream = io.BytesIO(raw_bytes)
        extractor = GitMetricExtractor(repo_path=self.random_repo_path, inspector=mock_inspector)

        result = extractor.parse_diff_stream(mock_stream)
        self.assertEqual(result["additions"], adds)
        self.assertEqual(result["deletions"], dels)
        self.assertEqual(result["total_churn"], adds + dels)
        self.assertIn(random_file, result["files_changed"])


if __name__ == "__main__":
    unittest.main()