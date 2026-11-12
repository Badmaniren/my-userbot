import io
import json
import random
import string
import unittest
import uuid
from unittest.mock import MagicMock, mock_open, patch

from skills.repo_health_trend_calculator import RepoHealthTrendCalculator


def get_random_str(length=12):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def get_random_metric_name():
    return f"metric_{uuid.uuid4().hex[:10]}"


def generate_snapshot(metric_keys, custom_values=None):
    custom_values = custom_values or {}
    metrics = {}
    for key in metric_keys:
        if key in custom_values:
            metrics[key] = custom_values[key]
        else:
            metrics[key] = round(random.uniform(5.0, 95.0), 2)

    return {
        "snapshot_id": f"snap_{uuid.uuid4().hex}",
        "timestamp": f"2026-0{random.randint(1, 9)}-{random.randint(10, 28)}T12:00:00Z",
        "metrics": metrics,
    }


class TestRepoHealthTrendCalculator(unittest.TestCase):

    def setUp(self):
        self.window_size = random.randint(3, 8)
        self.smoothing_factor = round(random.uniform(0.1, 0.9), 2)
        self.calculator = RepoHealthTrendCalculator(
            window_size=self.window_size,
            smoothing_factor=self.smoothing_factor
        )

    def test_calculate_metric_trend_improving(self):
        metric_name = get_random_metric_name()
        start_val = random.uniform(10.0, 30.0)
        increment = random.uniform(2.0, 5.0)

        history = []
        for i in range(6):
            val = round(start_val + (i * increment), 2)
            history.append(generate_snapshot([metric_name], {metric_name: val}))

        result = self.calculator.calculate_metric_trend(history, metric_name)

        self.assertEqual(result["metric"], metric_name)
        self.assertEqual(result["direction"], "improving")
        self.assertGreater(result["change_percentage"], 0.0)
        self.assertAlmostEqual(result["latest_value"], history[-1]["metrics"][metric_name], places=2)

    def test_calculate_metric_trend_degrading(self):
        metric_name = get_random_metric_name()
        start_val = random.uniform(70.0, 100.0)
        decrement = random.uniform(3.0, 7.0)

        history = []
        for i in range(6):
            val = round(start_val - (i * decrement), 2)
            history.append(generate_snapshot([metric_name], {metric_name: val}))

        result = self.calculator.calculate_metric_trend(history, metric_name)

        self.assertEqual(result["metric"], metric_name)
        self.assertEqual(result["direction"], "degrading")
        self.assertLess(result["change_percentage"], 0.0)
        self.assertAlmostEqual(result["latest_value"], history[-1]["metrics"][metric_name], places=2)

    def test_calculate_metric_trend_empty_history_raises_error(self):
        metric_name = get_random_metric_name()
        empty_history = []

        with self.assertRaises((ValueError, KeyError)):
            self.calculator.calculate_metric_trend(empty_history, metric_name)

    def test_calculate_metric_trend_missing_metric_raises_key_error(self):
        target_metric = get_random_metric_name()
        other_metric = f"other_{uuid.uuid4().hex[:8]}"

        history = [generate_snapshot([other_metric]) for _ in range(4)]

        with self.assertRaises((KeyError, ValueError)):
            self.calculator.calculate_metric_trend(history, target_metric)

    def test_detect_metric_anomalies_identifies_spike(self):
        metric_name = get_random_metric_name()
        base_val = random.uniform(40.0, 50.0)

        history = []
        for _ in range(8):
            noise = random.uniform(-0.5, 0.5)
            history.append(generate_snapshot([metric_name], {metric_name: round(base_val + noise, 2)}))

        anomaly_index = random.randint(2, 6)
        outlier_id = history[anomaly_index]["snapshot_id"]
        outlier_value = base_val + round(random.uniform(200.0, 500.0), 2)
        history[anomaly_index]["metrics"][metric_name] = outlier_value

        z_threshold = 2.0
        anomalies = self.calculator.detect_metric_anomalies(
            history, metric_name, z_threshold=z_threshold
        )

        detected_ids = [item["snapshot_id"] for item in anomalies]
        self.assertIn(outlier_id, detected_ids)

    def test_load_history_from_file_parses_json_stream(self):
        metric_name = get_random_metric_name()
        expected_snap_id = f"snap_{uuid.uuid4().hex}"
        expected_score = round(random.uniform(60.0, 99.0), 2)

        raw_data = [
            {
                "snapshot_id": expected_snap_id,
                "timestamp": "2026-03-30T10:00:00Z",
                "metrics": {metric_name: expected_score},
            }
        ]
        json_bytes = json.dumps(raw_data).encode("utf-8")
        random_file_path = f"/tmp/test_dir_{get_random_str()}/{uuid.uuid4().hex}.json"

        with patch("builtins.open", return_value=io.BytesIO(json_bytes)):
            with patch("os.path.exists", return_value=True):
                loaded_data = self.calculator.load_history_from_file(random_file_path)

        self.assertEqual(len(loaded_data), 1)
        self.assertEqual(loaded_data[0]["snapshot_id"], expected_snap_id)
        self.assertEqual(loaded_data[0]["metrics"][metric_name], expected_score)

    def test_export_trend_summary_writes_valid_structure(self):
        metric_1 = get_random_metric_name()
        metric_2 = get_random_metric_name()
        history = [generate_snapshot([metric_1, metric_2]) for _ in range(5)]

        random_output_path = f"/tmp/export_{get_random_str()}/{uuid.uuid4().hex}.json"
        mock_file = mock_open()

        with patch("builtins.open", mock_file):
            with patch("os.makedirs"):
                status = self.calculator.export_trend_summary(history, random_output_path)

        self.assertTrue(status)
        mock_file.assert_called_once_with(random_output_path, "w", encoding="utf-8")
        
        handle = mock_file()
        written_payload = "".join(call.args[0] for call in handle.write.call_args_list)
        self.assertIn(metric_1, written_payload)
        self.assertIn(metric_2, written_payload)

    def test_calculate_overall_trend_aggregates_multiple_metrics(self):
        m1 = get_random_metric_name()
        m2 = get_random_metric_name()
        history = [generate_snapshot([m1, m2]) for _ in range(5)]

        summary = self.calculator.calculate_overall_trend(history)

        self.assertIn("overall_status", summary)
        self.assertIn("metric_summaries", summary)
        self.assertIn(m1, summary["metric_summaries"])
        self.assertIn(m2, summary["metric_summaries"])

    def test_exponential_smoothing_returns_valid_trend_line(self):
        metric_name = get_random_metric_name()
        values = [round(random.uniform(10.0, 90.0), 2) for _ in range(7)]
        history = [generate_snapshot([metric_name], {metric_name: v}) for v in values]

        smoothed = self.calculator.get_smoothed_series(history, metric_name)

        self.assertEqual(len(smoothed), len(values))
        self.assertAlmostEqual(smoothed[0], values[0], places=2)


if __name__ == "__main__":
    unittest.main()