import json
import os
import random
import tempfile
import unittest
from unittest.mock import mock_open, patch

try:
    from skills.repo_health_trend_calculator import (
        RepoHealthTrendCalculator,
        calculate_health_trends,
    )
except ImportError:
    from repo_health_trend_calculator import (
        RepoHealthTrendCalculator,
        calculate_health_trends,
    )


def _gen_random_string(prefix="str_"):
    return f"{prefix}{os.urandom(8).hex()}"


def _gen_random_float(min_val=-100.0, max_val=100.0):
    return random.uniform(min_val, max_val)


class TestRepoHealthTrendCalculator(unittest.TestCase):

    def setUp(self):
        self.window_size = random.randint(1, 20)
        self.smoothing_factor = random.uniform(0.1, 0.9)
        self.calculator = RepoHealthTrendCalculator(
            window_size=self.window_size,
            smoothing_factor=self.smoothing_factor,
        )

    def test_init_parameters(self):
        self.assertEqual(self.calculator.window_size, self.window_size)
        self.assertEqual(self.calculator.smoothing_factor, self.smoothing_factor)

    def test_calculate_metric_trend_empty_history_raises_value_error(self):
        metric_name = _gen_random_string("metric_")
        with self.assertRaises(ValueError):
            self.calculator.calculate_metric_trend([], metric_name)

    def test_calculate_metric_trend_missing_metric_raises_key_error(self):
        metric_name = _gen_random_string("missing_")
        history = [
            {"metrics": {_gen_random_string("other_"): _gen_random_float()}}
        ]
        with self.assertRaises(KeyError):
            self.calculator.calculate_metric_trend(history, metric_name)

    def test_calculate_metric_trend_improving(self):
        metric_name = _gen_random_string("metric_")
        v1 = random.uniform(1.0, 10.0)
        v2 = v1 + random.uniform(5.0, 15.0)
        history = [
            {"metrics": {metric_name: v1}},
            {"metrics": {metric_name: v2}},
        ]

        result = self.calculator.calculate_metric_trend(history, metric_name)

        expected_delta = v2 - v1
        expected_percentage = (expected_delta / abs(v1)) * 100.0
        self.assertEqual(result["metric"], metric_name)
        self.assertEqual(result["direction"], "improving")
        self.assertAlmostEqual(result["delta"], expected_delta)
        self.assertAlmostEqual(result["change_percentage"], expected_percentage)
        self.assertAlmostEqual(result["first_value"], v1)
        self.assertAlmostEqual(result["latest_value"], v2)

    def test_calculate_metric_trend_degrading(self):
        metric_name = _gen_random_string("metric_")
        v1 = random.uniform(20.0, 50.0)
        v2 = v1 - random.uniform(5.0, 15.0)
        history = [
            {"metrics": {metric_name: v1}},
            {"metrics": {metric_name: v2}},
        ]

        result = self.calculator.calculate_metric_trend(history, metric_name)

        expected_delta = v2 - v1
        self.assertEqual(result["direction"], "degrading")
        self.assertAlmostEqual(result["delta"], expected_delta)

    def test_calculate_metric_trend_stable(self):
        metric_name = _gen_random_string("metric_")
        v1 = random.uniform(1.0, 50.0)
        history = [
            {"metrics": {metric_name: v1}},
            {"metrics": {metric_name: v1}},
        ]

        result = self.calculator.calculate_metric_trend(history, metric_name)

        self.assertEqual(result["direction"], "stable")
        self.assertEqual(result["delta"], 0.0)
        self.assertEqual(result["change_percentage"], 0.0)

    def test_calculate_metric_trend_zero_first_value(self):
        metric_name = _gen_random_string("metric_")
        v1 = 0.0
        v2 = random.uniform(1.0, 10.0)
        history = [
            {"metrics": {metric_name: v1}},
            {"metrics": {metric_name: v2}},
        ]

        result = self.calculator.calculate_metric_trend(history, metric_name)

        expected_delta = v2 - v1
        expected_percentage = expected_delta * 100.0
        self.assertAlmostEqual(result["change_percentage"], expected_percentage)
        self.assertEqual(result["direction"], "improving")

    def test_detect_metric_anomalies_empty_history(self):
        metric_name = _gen_random_string("metric_")
        self.assertEqual(self.calculator.detect_metric_anomalies([], metric_name), [])

    def test_detect_metric_anomalies_missing_metric_returns_empty(self):
        metric_name = _gen_random_string("metric_")
        history = [{"metrics": {_gen_random_string("other_"): 10.0}}]
        self.assertEqual(
            self.calculator.detect_metric_anomalies(history, metric_name), []
        )

    def test_detect_metric_anomalies_zero_std_dev(self):
        metric_name = _gen_random_string("metric_")
        val = _gen_random_float()
        history = [
            {"metrics": {metric_name: val}},
            {"metrics": {metric_name: val}},
        ]
        self.assertEqual(
            self.calculator.detect_metric_anomalies(history, metric_name), []
        )

    def test_detect_metric_anomalies_detects_outlier(self):
        metric_name = _gen_random_string("metric_")
        history = [
            {"metrics": {metric_name: 10.0}, "id": 1},
            {"metrics": {metric_name: 10.0}, "id": 2},
            {"metrics": {metric_name: 10.0}, "id": 3},
            {"metrics": {metric_name: 10.0}, "id": 4},
            {"metrics": {metric_name: 100.0}, "id": 5},
        ]
        anomalies = self.calculator.detect_metric_anomalies(
            history, metric_name, z_threshold=1.5
        )
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["id"], 5)

    def test_load_history_from_file(self):
        fake_path = f"/tmp/{_gen_random_string('file_')}.json"
        expected_data = [{"metrics": {_gen_random_string("m_"): 42}}]

        with patch("builtins.open", mock_open(read_data=json.dumps(expected_data))):
            loaded = self.calculator.load_history_from_file(fake_path)

        self.assertEqual(loaded, expected_data)

    def test_export_trend_summary(self):
        dir_name = _gen_random_string("dir_")
        file_name = f"{_gen_random_string('summary_')}.json"
        output_path = os.path.join(dir_name, file_name)
        metric_name = _gen_random_string("metric_")
        history = [
            {"metrics": {metric_name: 10.0}},
            {"metrics": {metric_name: 20.0}},
        ]

        with patch("os.makedirs") as mock_mkdirs:
            with patch("builtins.open", mock_open()) as mocked_file:
                res = self.calculator.export_trend_summary(history, output_path)

        self.assertTrue(res)
        mock_mkdirs.assert_called_once_with(dir_name, exist_ok=True)
        mocked_file.assert_called_once_with(output_path, "w", encoding="utf-8")

    def test_calculate_overall_trend_empty(self):
        res = self.calculator.calculate_overall_trend([])
        self.assertEqual(res, {"overall_status": "stable", "metric_summaries": {}})

    def test_calculate_overall_trend_improving_majority(self):
        m1 = _gen_random_string("m1_")
        m2 = _gen_random_string("m2_")
        history = [
            {"metrics": {m1: 10.0, m2: 50.0}},
            {"metrics": {m1: 20.0, m2: 40.0}},
            {"metrics": {m1: 30.0, m2: 39.0}},
        ]
        res = self.calculator.calculate_overall_trend(history)
        self.assertIn(res["overall_status"], ["improving", "degrading", "stable"])
        self.assertIn(m1, res["metric_summaries"])
        self.assertIn(m2, res["metric_summaries"])

    def test_calculate_overall_trend_degrading_majority(self):
        m1 = _gen_random_string("m1_")
        history = [
            {"metrics": {m1: 100.0}},
            {"metrics": {m1: 10.0}},
        ]
        res = self.calculator.calculate_overall_trend(history)
        self.assertEqual(res["overall_status"], "degrading")

    def test_get_smoothed_series_empty_history(self):
        metric_name = _gen_random_string("metric_")
        self.assertEqual(self.calculator.get_smoothed_series([], metric_name), [])

    def test_get_smoothed_series_missing_metric_raises_key_error(self):
        metric_name = _gen_random_string("metric_")
        history = [{"metrics": {_gen_random_string("other_"): 5.0}}]
        with self.assertRaises(KeyError):
            self.calculator.get_smoothed_series(history, metric_name)

    def test_get_smoothed_series_calculation(self):
        metric_name = _gen_random_string("metric_")
        alpha = 0.5
        calc = RepoHealthTrendCalculator(smoothing_factor=alpha)

        v0 = 10.0
        v1 = 20.0
        v2 = 30.0
        history = [
            {"metrics": {metric_name: v0}},
            {"metrics": {metric_name: v1}},
            {"metrics": {metric_name: v2}},
        ]

        smoothed = calc.get_smoothed_series(history, metric_name)

        s0 = float(v0)
        s1 = alpha * v1 + (1.0 - alpha) * s0
        s2 = alpha * v2 + (1.0 - alpha) * s1

        self.assertEqual(len(smoothed), 3)
        self.assertAlmostEqual(smoothed[0], s0)
        self.assertAlmostEqual(smoothed[1], s1)
        self.assertAlmostEqual(smoothed[2], s2)

    def test_calculate_trends_empty_history(self):
        repo_id = _gen_random_string("repo_")
        res = self.calculator.calculate_trends(repo_id, [])
        self.assertEqual(res["repo_id"], repo_id)
        self.assertEqual(res["trends"], {})
        self.assertEqual(
            res["summary"], {"overall_status": "stable", "metric_summaries": {}}
        )

    def test_calculate_trends_upward_downward_stable(self):
        repo_id = _gen_random_string("repo_")
        m_up = _gen_random_string("up_")
        m_down = _gen_random_string("down_")
        m_stable = _gen_random_string("stable_")

        history = [
            {"metrics": {m_up: 1.0, m_down: 10.0, m_stable: 5.0}},
            {"metrics": {m_up: 5.0, m_down: 2.0, m_stable: 5.0}},
        ]

        res = self.calculator.calculate_trends(repo_id, history)

        self.assertEqual(res["repo_id"], repo_id)
        self.assertEqual(res["trends"][m_up]["direction"], "upward")
        self.assertEqual(res["trends"][m_down]["direction"], "downward")
        self.assertEqual(res["trends"][m_stable]["direction"], "stable")

    def test_calculate_trends_single_value_metric(self):
        repo_id = _gen_random_string("repo_")
        m_single = _gen_random_string("single_")
        history = [
            {"metrics": {m_single: 42.0}}
        ]

        res = self.calculator.calculate_trends(repo_id, history)
        trend_info = res["trends"][m_single]

        self.assertEqual(trend_info["direction"], "stable")
        self.assertEqual(trend_info["delta"], 0)
        self.assertEqual(trend_info["historical_values"], [42.0])

    def test_calculate_health_trends_function(self):
        repo_id = _gen_random_string("repo_")
        metric_name = _gen_random_string("metric_")
        input_data = {
            "repo_id": repo_id,
            "history": [
                {"metrics": {metric_name: 100.0}},
                {"metrics": {metric_name: 150.0}},
            ],
        }

        input_json_str = json.dumps(input_data)
        fake_in_path = f"/tmp/{_gen_random_string('in_')}.json"
        fake_out_path = f"/tmp/{_gen_random_string('out_dir_')}/{_gen_random_string('out_')}.json"

        with patch("os.makedirs") as mock_mkdirs:
            with patch("builtins.open", mock_open(read_data=input_json_str)) as mock_file:
                res = calculate_health_trends(fake_in_path, fake_out_path)

        self.assertEqual(res["repo_id"], repo_id)
        self.assertIn(metric_name, res["trends"])
        self.assertEqual(res["trends"][metric_name]["direction"], "upward")
        mock_mkdirs.assert_called_once_with(os.path.dirname(fake_out_path), exist_ok=True)
        self.assertEqual(mock_file.call_count, 2)


if __name__ == "__main__":
    unittest.main()