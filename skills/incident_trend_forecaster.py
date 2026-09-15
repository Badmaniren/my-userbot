from skills import incident_trend_analyzer
from skills import patch_metric_collector


class IncidentTrendForecaster:

    def forecast_future_incidents(self, module_name: str) -> dict:
        analyzer = incident_trend_analyzer.IncidentTrendAnalyzer()
        trend_result = analyzer.analyze_trends(module_name)
        return {
            "module_name": module_name,
            "trend_data": trend_result
        }

    def _extract_trends_from_analyzer(self, module_name: str) -> dict:
        analyzer = incident_trend_analyzer.IncidentTrendAnalyzer()
        return analyzer.analyze_trends(module_name)

    def gather_metrics_and_trends(self, module_name: str) -> dict:
        collector = patch_metric_collector.PatchMetricCollector()
        metrics_summary = collector.get_metrics_summary(module_name)
        trend_data = self._extract_trends_from_analyzer(module_name)
        return {
            "module_name": module_name,
            "metrics_summary": metrics_summary,
            "trend_data": trend_data
        }

    def predict_next_failure_window(self, module_name: str) -> dict:
        analyzer = incident_trend_analyzer.IncidentTrendAnalyzer()
        collector = patch_metric_collector.PatchMetricCollector()

        trend_payload = analyzer.analyze_trends(module_name)
        collector.get_metrics_summary(module_name)

        if not isinstance(trend_payload, dict):
            trend_payload = {}

        incidents_count = trend_payload.get("incidents_history_count", 0)
        avg_recovery = trend_payload.get("average_recovery_time_seconds", 10.0)
        weights = trend_payload.get("severity_weights", [1])

        if not weights:
            weights = [1]

        risk_score = sum(weights) / max(1, incidents_count) if incidents_count > 0 else 0.5
        estimated_time = max(0.0, float(avg_recovery) / (risk_score + 0.1))

        if risk_score > 5.0:
            risk_level = "HIGH"
        elif risk_score > 2.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "analyzed_module": module_name,
            "predicted_risk_level": risk_level,
            "estimated_time_to_failure": estimated_time
        }

    def process_stream_and_forecast(self, module_name: str, stream_bytes) -> dict:
        analyzer = incident_trend_analyzer.IncidentTrendAnalyzer()
        stream_context = analyzer.parse_stream_data(stream_bytes)
        return {
            "module_name": module_name,
            "stream_context": stream_context
        }

    def export_forecast_report(self, payload: dict, output_path: str, format_type: str) -> bool:
        dashboard_gen = incident_trend_analyzer.RecoveryDashboardGenerator()
        success = dashboard_gen.export_dashboard(payload, output_path, format_type)
        return bool(success)

    def forecast_trends(self, module_name: str) -> dict:
        analyzer = incident_trend_analyzer.IncidentTrendAnalyzer()
        trend_data = analyzer.analyze_trends(module_name)
        return {
            "module_name": module_name,
            "forecast": "stable",
            "trend_data": trend_data
        }