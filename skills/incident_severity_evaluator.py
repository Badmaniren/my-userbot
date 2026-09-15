from skills.incident_aggregator import IncidentAggregator
from skills.incident_trend_forecaster import IncidentTrendForecaster


class IncidentSeverityEvaluator:
    def __init__(self):
        self.aggregator = IncidentAggregator()
        self.forecaster = IncidentTrendForecaster()

    def evaluate(self, module_name, exception, traceback_str, incident_id):
        exc_obj = exception if isinstance(exception, Exception) else Exception(str(exception))
        aggregation = self.aggregator.process_and_aggregate(
            module_name, exc_obj, traceback_str, incident_id
        )
        forecast = self.forecaster.forecast_future_incidents(module_name)

        score = aggregation.get("severity_score", 0)
        multiplier = forecast.get("risk_multiplier", 1.0)
        final_severity_index = score * multiplier

        return {
            "aggregation": aggregation,
            "forecast": forecast,
            "final_severity_index": final_severity_index
        }

    def evaluate_stream(self, module_name, stream_mock):
        return self.forecaster.process_stream_and_forecast(module_name, stream_mock)


def evaluate_incident_severity(module_name, exception, traceback_str, incident_id):
    aggregator = IncidentAggregator()
    forecaster = IncidentTrendForecaster()

    exc_obj = exception if isinstance(exception, Exception) else Exception(str(exception))

    agg_result = aggregator.process_and_aggregate(
        module_name, exc_obj, traceback_str, incident_id
    )

    forecast_result = {}
    if hasattr(forecaster, 'forecast_trends'):
        forecast_result = forecaster.forecast_trends(module_name)
    elif hasattr(forecaster, 'forecast_future_incidents'):
        forecast_result = forecaster.forecast_future_incidents(module_name)

    base_id = incident_id or agg_result.get("id") or agg_result.get("incident_id")
    severity_score = agg_result.get("severity_score") or agg_result.get("load") or 10

    result = {
        "incident_id": base_id,
        "severity_rating": severity_score,
        "severity_score": severity_score,
        "trend_metrics": forecast_result,
        "aggregated_data": agg_result,
    }
    return result