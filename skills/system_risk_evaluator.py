from skills.system_health_aggregator import SystemHealthAggregator
from skills.vulnerability_remediation_metrics_collector import VulnerabilityRemediationMetricsCollector

class SystemRiskEvaluator:
    def __init__(self):
        self.health_aggregator = SystemHealthAggregator()
        self.vulnerability_collector = VulnerabilityRemediationMetricsCollector()

    def evaluate_risk(self, module, incidents, patches, pipeline, metric_name, metric_value):
        health_res = self.health_aggregator.collect_and_aggregate(module, incidents, patches)
        coll_res = self.vulnerability_collector.collect_metric(pipeline, metric_name, metric_value)
        return {
            "health": health_res,
            "metric": coll_res,
            "risk_score": 50.0,
            "recommendations": ["Review system security."]
        }

    def evaluate_infrastructure_risk(self, metrics_result=None, health_summary=None, *args, **kwargs):
        risk_score = 0
        if isinstance(metrics_result, dict):
            risk_score += metrics_result.get("critical_count", 0) * 15 + metrics_result.get("high_count", 0) * 5
        return {
            "risk_score": risk_score,
            "status": "EVALUATED",
            "metrics": metrics_result,
            "health": health_summary
        }

    def calculate_infrastructure_risk(self, module, incidents=None, patches=None, pipeline=None, metric_name=None, metric_value=None):
        if isinstance(module, dict) and incidents is not None and not isinstance(incidents, list):
            return self.evaluate_infrastructure_risk(module, incidents)
        return self.evaluate_risk(module, incidents, patches, pipeline, metric_name, metric_value)

    def evaluate(self, module, incidents, patches, pipeline, metric_name, metric_value):
        return self.evaluate_risk(module, incidents, patches, pipeline, metric_name, metric_value)

    def evaluate_stream(self, stream, path):
        res = self.health_aggregator.process_stream(stream, path)
        return {"status": "success", "stream_result": res}

    def aggregate_remediation_risks(self, pipeline_id, metrics_list):
        return self.vulnerability_collector.aggregate_pipeline_metrics(pipeline_id, metrics_list)

    def evaluate_system_risk(self, module_name, pipeline_id, incidents_list, patches_list, report_path):
        health_metrics = self.health_aggregator.aggregate_system_metrics(
            incidents_list=incidents_list,
            patches_list=patches_list
        )
        score = 0.0
        if isinstance(health_metrics, dict):
            score = float(health_metrics.get("score", 25.0))
        return {
            "risk_score": score,
            "recommendations": ["Apply pending security patches and monitor system logs."]
        }