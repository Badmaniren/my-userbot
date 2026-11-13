import json
import os


class RepoHealthTrendCalculator:
    """Calculates repository health metric trends and dynamics based on stored snapshot history."""

    def __init__(self, window_size=5, smoothing_factor=0.5):
        self.window_size = window_size
        self.smoothing_factor = smoothing_factor

    def calculate_metric_trend(self, history, metric_name):
        if not history:
            raise ValueError("History cannot be empty")

        values = []
        for snapshot in history:
            metrics = snapshot.get("metrics", {})
            if metric_name not in metrics:
                raise KeyError(f"Metric '{metric_name}' missing from snapshot")
            values.append(metrics[metric_name])

        if not values:
            raise KeyError(f"Metric '{metric_name}' not found in history")

        first_value = values[0]
        latest_value = values[-1]
        delta = latest_value - first_value

        if first_value != 0:
            change_percentage = (delta / abs(first_value)) * 100.0
        else:
            change_percentage = delta * 100.0

        if change_percentage > 0:
            direction = "improving"
        elif change_percentage < 0:
            direction = "degrading"
        else:
            direction = "stable"

        return {
            "metric": metric_name,
            "direction": direction,
            "change_percentage": change_percentage,
            "latest_value": latest_value,
            "first_value": first_value,
            "delta": delta,
        }

    def detect_metric_anomalies(self, history, metric_name, z_threshold=2.0):
        if not history:
            return []

        values = []
        for snapshot in history:
            metrics = snapshot.get("metrics", {})
            if metric_name in metrics:
                values.append(metrics[metric_name])

        if not values:
            return []

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5

        if std_dev == 0:
            return []

        anomalies = []
        for snapshot in history:
            metrics = snapshot.get("metrics", {})
            if metric_name in metrics:
                val = metrics[metric_name]
                z_score = abs(val - mean) / std_dev
                if z_score >= z_threshold:
                    anomalies.append(snapshot)

        return anomalies

    def load_history_from_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def export_trend_summary(self, history, output_path):
        dir_path = os.path.dirname(output_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        summary = self.calculate_overall_trend(history)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return True

    def calculate_overall_trend(self, history):
        if not history:
            return {"overall_status": "stable", "metric_summaries": {}}

        metric_keys = set()
        for snapshot in history:
            if isinstance(snapshot, dict) and "metrics" in snapshot and isinstance(snapshot["metrics"], dict):
                metric_keys.update(snapshot["metrics"].keys())

        metric_summaries = {}
        improving_count = 0
        degrading_count = 0

        for key in metric_keys:
            trend = self.calculate_metric_trend(history, key)
            metric_summaries[key] = trend
            if trend["direction"] == "improving":
                improving_count += 1
            elif trend["direction"] == "degrading":
                degrading_count += 1

        if improving_count > degrading_count:
            overall_status = "improving"
        elif degrading_count > improving_count:
            overall_status = "degrading"
        else:
            overall_status = "stable"

        return {
            "overall_status": overall_status,
            "metric_summaries": metric_summaries,
        }

    def get_smoothed_series(self, history, metric_name):
        if not history:
            return []

        values = []
        for snapshot in history:
            metrics = snapshot.get("metrics", {})
            if metric_name not in metrics:
                raise KeyError(f"Metric '{metric_name}' missing from snapshot")
            values.append(metrics[metric_name])

        smoothed = []
        for i, val in enumerate(values):
            if i == 0:
                smoothed.append(float(val))
            else:
                prev = smoothed[-1]
                smoothed_val = self.smoothing_factor * val + (1.0 - self.smoothing_factor) * prev
                smoothed.append(float(smoothed_val))

        return smoothed

    def calculate_trends(self, repo_id, history):
        if not history:
            return {
                "repo_id": repo_id,
                "trends": {},
                "summary": {"overall_status": "stable", "metric_summaries": {}},
            }

        metric_keys = set()
        for snapshot in history:
            if isinstance(snapshot, dict) and "metrics" in snapshot and isinstance(snapshot["metrics"], dict):
                metric_keys.update(snapshot["metrics"].keys())

        trends = {}
        for key in metric_keys:
            vals = [
                snap["metrics"][key]
                for snap in history
                if isinstance(snap, dict) and "metrics" in snap and key in snap["metrics"]
            ]
            if len(vals) <= 1:
                delta = 0
                direction = "stable"
            else:
                delta = vals[-1] - vals[0]
                if delta > 0:
                    direction = "upward"
                elif delta < 0:
                    direction = "downward"
                else:
                    direction = "stable"

            trends[key] = {
                "direction": direction,
                "delta": delta,
                "historical_values": vals,
            }

        summary = self.calculate_overall_trend(history)
        return {
            "repo_id": repo_id,
            "trends": trends,
            "summary": summary,
        }


def calculate_health_trends(input_file, output_file):
    calculator = RepoHealthTrendCalculator()
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    repo_id = data.get("repo_id", "")
    history = data.get("history", [])

    result = calculator.calculate_trends(repo_id=repo_id, history=history)

    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    else:
        os.makedirs(".", exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result