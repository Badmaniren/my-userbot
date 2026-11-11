from skills.repo_security_gateway import RepoSecurityGateway
from skills.repo_health_metric_validator import (
    RepoHealthMetricValidator,
    MetricValidationError,
)

class RepoSecurityGateValidator:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.security_gateway = RepoSecurityGateway(repo_path)
        self.health_validator = RepoHealthMetricValidator()

    def validate_gate(self, metrics_data: dict) -> dict:
        errors = []
        reasons = []
        failures = []
        
        sec_eval = {}
        health_eval = {"valid": False}
        
        passed_security = False
        passed_health = False

        try:
            sec_eval = self.security_gateway.scan_and_evaluate()
            if isinstance(sec_eval, dict):
                passed_security = sec_eval.get("passed", True)
                if not passed_security:
                    reason = sec_eval.get("reason", "Security check failed")
                    reasons.append(reason)
                    errors.append(reason)
            else:
                passed_security = False
                reasons.append("Invalid security evaluation response")
                errors.append("Invalid security evaluation response")
        except Exception as e:
            err_msg = str(e)
            reasons.append(err_msg)
            errors.append(err_msg)
            sec_eval = {"passed": False, "status": "FAIL", "reason": err_msg}
            passed_security = False

        try:
            health_res = self.health_validator.validate(metrics_data)
            if isinstance(health_res, dict):
                passed_health = health_res.get("valid", True)
                health_eval = health_res
            else:
                passed_health = bool(health_res)
                health_eval = {"valid": passed_health}
        except MetricValidationError as mve:
            err_msg = str(mve)
            reasons.append(err_msg)
            errors.append(err_msg)
            failures.append(err_msg)
            health_eval = {"valid": False, "error": err_msg}
            passed_health = False
        except Exception as e:
            err_msg = str(e)
            reasons.append(err_msg)
            errors.append(err_msg)
            failures.append(err_msg)
            health_eval = {"valid": False, "error": err_msg}
            passed_health = False

        overall_passed = passed_security and passed_health
        blocked = not overall_passed

        run_id = metrics_data.get("run_id") if isinstance(metrics_data, dict) else None

        result = {
            "passed": overall_passed,
            "allowed": overall_passed,
            "blocked": blocked,
            "security_evaluation": sec_eval,
            "security_gate": sec_eval,
            "health_evaluation": health_eval,
            "errors": errors,
            "reasons": reasons,
            "failures": failures,
            "audit_record": str(metrics_data) if metrics_data else "",
        }
        
        if run_id:
            result["run_id"] = run_id
            
        return result

    def validate_stream_gate(self, stream_io) -> dict:
        try:
            parsed_items = self.health_validator.validate_stream(stream_io)
            metrics_payload = parsed_items[0] if parsed_items and isinstance(parsed_items, list) else {}
            res = self.validate_gate(metrics_payload)
            return res
        except Exception as e:
            err_msg = str(e)
            return {
                "passed": False,
                "allowed": False,
                "blocked": True,
                "errors": [err_msg],
                "reasons": [err_msg],
                "failures": [err_msg],
                "security_evaluation": {"passed": False},
                "security_gate": {"passed": False},
                "health_evaluation": {"valid": False, "error": err_msg},
                "audit_record": str(stream_io)
            }


def validate_repo_security_gate(repo_path: str, metrics_data: dict) -> dict:
    validator = RepoSecurityGateValidator(repo_path=repo_path)
    return validator.validate_gate(metrics_data)