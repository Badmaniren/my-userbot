import json
import requests
import statistics
from bs4 import BeautifulSoup
import os


class RepoHealthTrendAggregator:
    """
    Агрегирует временные ряды метрик здоровья репозитория и данные инцидентов.
    """

    def aggregate_time_series(self, time_series):
        if not time_series:
            return {}

        aggregated = {}
        for entry in time_series:
            metric_name = entry.get("metric_name")
            value = entry.get("value")

            if not metric_name or not isinstance(value, (int, float)):
                continue

            if metric_name not in aggregated:
                aggregated[metric_name] = {"values": []}
            aggregated[metric_name]["values"].append(value)

        result = {}
        for name, data in aggregated.items():
            vals = data["values"]
            result[name] = {
                "count": len(vals),
                "mean": statistics.mean(vals),
                "min": min(vals),
                "max": max(vals)
            }
        return result

    def aggregate_incidents(self, incidents):
        summary = {"by_severity": {}, "total_incidents": len(incidents)}
        for inc in incidents:
            sev = inc.get("severity")
            summary["by_severity"][sev] = summary["by_severity"].get(sev, 0) + 1
        return summary

    def merge_metrics_and_incidents(self, metrics_summary, incident_summary):
        return {
            "metrics": metrics_summary,
            "incidents": incident_summary
        }

    def calculate_trend_indicators(self, aggregated_data):
        results = {}
        for name, data in aggregated_data.get("metrics", {}).items():
            series = data.get("series", [])
            if len(series) >= 2 and series[-1] > series[0]:
                direction = "UPWARD"
            else:
                direction = "STABLE"
            results[name] = {"direction": direction}
        return results

    def fetch_external_health_data(self, url):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception:
            return None
        return None

    def export_prepared_dataset(self, dataset, file_path):
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(dataset, f)
            return True
        except IOError:
            return False

    def parse_html_health_report(self, stream):
        soup = BeautifulSoup(stream, "html.parser")
        incidents = []
        for item in soup.find_all("div", class_="incident-item"):
            incidents.append({
                "id": item.get("id"),
                "title": item.find("span", class_="title").text
            })
        return incidents

    def aggregate(self, repo_id, data_dir):
        """
        Интеграционный метод для обработки данных репозитория.
        """
        metrics = []

        # Читаем файлы метрик
        for filename in os.listdir(data_dir):
            if filename.startswith("metrics_"):
                with open(os.path.join(data_dir, filename), 'r') as f:
                    metrics.append(json.load(f))

        from skills.repo_health_incident_tracker import RepoHealthIncidentTracker
        tracker = RepoHealthIncidentTracker()
        if hasattr(tracker, "get_incidents_by_repo"):
            incidents = tracker.get_incidents_by_repo(repo_id)
        elif hasattr(tracker, "list_incidents_by_repo"):
            incidents = tracker.list_incidents_by_repo(repo_id)
        else:
            incidents = []
        incident_ids = [inc.get("incident_id") or inc.get("id") for inc in incidents]

        result = {
            "repo_id": repo_id,
            "metric_id": metrics[0]['metric_id'] if metrics else None,
            "processed_metrics": [m['metric_id'] for m in metrics],
            "associated_incidents": incident_ids
        }

        output_path = os.path.join(data_dir, "trend_summary.json")
        with open(output_path, 'w') as f:
            json.dump(result, f)

        return result