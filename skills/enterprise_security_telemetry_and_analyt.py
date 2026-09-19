"""
Enterprise Security Telemetry and Analytics Pipeline Skill Module
"""

from skills.vulnerability_remediation_metrics_collector import VulnerabilityRemediationMetricsCollector
from skills.vulnerability_remediation_audit_exporter import VulnerabilityRemediationAuditExporter
from skills.vulnerability_remediation_pipeline import VulnerabilityRemediationPipeline
from skills.system_risk_evaluator import SystemRiskEvaluator
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector


class EnterpriseSecurityTelemetryAndAnalytics:
    def __init__(self):
        self.metrics_collector = VulnerabilityRemediationMetricsCollector()
        self.audit_exporter = VulnerabilityRemediationAuditExporter()
        self.remediation_pipeline = VulnerabilityRemediationPipeline()
        self.risk_evaluator = SystemRiskEvaluator()
        self.health_collector = SystemHealthTelemetryCollector()

    def process_telemetry_and_eval_risk(self, telemetry_payload):
        metrics_result = self.metrics_collector.collect(telemetry_payload)
        audit_export_result = self.audit_exporter.export_audit(telemetry_payload)
        pipeline_execution = self.remediation_pipeline.run_pipeline(telemetry_payload)
        health_summary = self.health_collector.aggregate(telemetry_payload)
        risk_assessment = self.risk_evaluator.evaluate_infrastructure_risk(metrics_result, health_summary)
        return {
            "metrics": metrics_result,
            "audit_export": audit_export_result,
            "pipeline_execution": pipeline_execution,
            "health_summary": health_summary,
            "risk_assessment": risk_assessment
        }


def execute_security_telemetry_pipeline(telemetry_payload):
    engine = EnterpriseSecurityTelemetryAndAnalytics()
    return engine.process_telemetry_and_eval_risk(telemetry_payload)


__all__ = [
    "VulnerabilityRemediationMetricsCollector",
    "VulnerabilityRemediationAuditExporter",
    "VulnerabilityRemediationPipeline",
    "SystemRiskEvaluator",
    "SystemHealthTelemetryCollector",
    "EnterpriseSecurityTelemetryAndAnalytics",
    "execute_security_telemetry_pipeline",
]
