import json
import datetime
from skills import market_portfolio_stress_audit_summary_vault
from skills import market_portfolio_realtime_stream_ingestor
from skills import market_portfolio_audit_log_exporter
from skills.db_storage import db_storage

class MarketPortfolioStressAuditComplianceValidator:
    def __init__(self):
        pass

    def validate_audit_compliance(self, audit_id, risk_threshold):
        audit_data = market_portfolio_stress_audit_summary_vault.fetch_audit_summary(audit_id)

        max_drawdown = audit_data.get("max_drawdown", 0.0)
        regulatory_status = audit_data.get("regulatory_status", "PENDING")

        violations = []
        if max_drawdown > risk_threshold:
            violations.append({
                "metric": "max_drawdown",
                "value": max_drawdown,
                "threshold": risk_threshold
            })

        is_compliant = (len(violations) == 0) and (regulatory_status == "COMPLIANT")

        result = {
            "audit_id": audit_id,
            "is_compliant": is_compliant,
            "compliance_timestamp": datetime.datetime.utcnow().isoformat(),
            "violations": violations
        }
        return result

    def process_stream_compliance(self, stream_token):
        stream_reader = market_portfolio_realtime_stream_ingestor.get_stream_reader(stream_token)
        raw_data = stream_reader.read()
        parsed_data = json.loads(raw_data.decode('utf-8'))

        return {
            "processed": True,
            "stream_id": parsed_data.get("stream_id", stream_token)
        }

    def _evaluate_single_rule(self, audit_payload, rule_definition):
        metric = rule_definition.get("metric")
        max_limit = rule_definition.get("max_limit")
        val = audit_payload.get(metric)

        if val is not None and max_limit is not None and val > max_limit:
            return {
                "metric": metric,
                "value": val,
                "max_limit": max_limit
            }
        return None

    def export_compliance_report(self, audit_result, export_target):
        response = market_portfolio_audit_log_exporter.push_audit_log(audit_result, export_target)
        return response


def market_portfolio_stress_audit_compliance_validator(vault_key):
    stored_vault = db_storage(vault_key)
    if not stored_vault:
        stored_vault = market_portfolio_stress_audit_summary_vault.fetch_audit_summary(vault_key)

    audit_id = stored_vault.get("audit_id")
    compliance_score = stored_vault.get("compliance_score", 100.0)

    is_compliant = compliance_score >= 50.0

    result = {
        "audit_id": audit_id,
        "is_compliant": is_compliant,
        "compliance_timestamp": datetime.datetime.utcnow().isoformat(),
        "violations": [] if is_compliant else [{"metric": "compliance_score", "value": compliance_score}]
    }

    db_storage(vault_key, result)
    return result