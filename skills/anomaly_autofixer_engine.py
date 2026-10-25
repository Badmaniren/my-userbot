import uuid
import json

class AnomalyAutofixerEngineError(Exception):
    """Исключение для модуля автоматического исправления аномалий."""
    pass


class AutofixRule:
    """Правило автоматического исправления аномалий."""
    def __init__(self, rule_id: str, pattern: str, action: str):
        self.rule_id = rule_id
        self.pattern = pattern
        self.action = action


class AnomalyAutofixerEngine:
    """Движок автоматического исправления аномалий на основе правил и телеметрии."""
    def __init__(self, telemetry_client=None):
        self.rules = []
        self.telemetry_client = telemetry_client

    def add_rule(self, rule: AutofixRule):
        self.rules.append(rule)

    def apply_fixes(self, anomaly_data: dict) -> dict:
        if not isinstance(anomaly_data, dict):
            raise AnomalyAutofixerEngineError("Invalid anomaly data format")

        details = anomaly_data.get("details", "")
        if isinstance(details, dict):
            details_str = json.dumps(details)
        else:
            details_str = str(details)

        applied = []
        for rule in self.rules:
            if rule.pattern in details_str:
                applied.append(rule.rule_id)

        return {
            "anomaly_id": anomaly_data.get("id", uuid.uuid4().hex),
            "fixed": len(applied) > 0,
            "applied_rules": applied
        }

    def execute_pipeline(self, telemetry_stream):
        if telemetry_stream is None:
            raise AnomalyAutofixerEngineError("Stream is None")
        content = telemetry_stream.read()
        if not content:
            return []
        return [{"status": "processed", "bytes_read": len(content)}]


def autofix_anomaly(source: str, severity: str, details: dict, telemetry: dict) -> dict:
    """Функция интеграционного уровня для автоисправления аномалий."""
    engine = AnomalyAutofixerEngine()

    default_rule = AutofixRule(
        rule_id=f"rule-{uuid.uuid4().hex[:6]}",
        pattern="",
        action="log_and_mitigate"
    )
    engine.add_rule(default_rule)

    payload = {
        "id": uuid.uuid4().hex,
        "source": source,
        "severity": severity,
        "details": details,
        "telemetry": telemetry
    }

    fix_res = engine.apply_fixes(payload)

    return {
        "status": "success" if fix_res["fixed"] or bool(fix_res["applied_rules"]) else "skipped",
        "anomaly_id": fix_res["anomaly_id"],
        "applied_rules": fix_res["applied_rules"]
    }