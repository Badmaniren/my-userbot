import re
from typing import Any, Dict, List, Optional, Union


class PatchRuleEngineError(Exception):
    """Base error for PatchRuleEngine operations."""
    pass


class RuleViolationError(PatchRuleEngineError):
    """Raised when a patch or telemetry violates declarative rules."""
    pass


class PatchRuleEngine:
    def __init__(
        self,
        name: Optional[str] = None,
        retries: int = 0,
        threshold: Optional[float] = None,
        rules: Optional[List[Dict[str, Any]]] = None,
        logger: Optional[Any] = None,
    ):
        self.name = name
        self.retries = retries
        self.threshold = threshold
        self.logger = logger
        self.rules: Dict[str, Dict[str, Any]] = {}
        self.threshold_rules: Dict[str, Dict[str, Any]] = {}

        if rules:
            for rule in rules:
                self.add_rule(rule)

    def add_rule(
        self,
        rule_or_id: Optional[Union[Dict[str, Any], str]] = None,
        rule_id: Optional[str] = None,
        pattern: Optional[str] = None,
        severity: str = "ERROR",
        **kwargs: Any,
    ) -> None:
        if isinstance(rule_or_id, dict):
            rule_dict = rule_or_id
            rid = rule_dict.get("id")
            if not rid:
                raise PatchRuleEngineError("Rule must have an 'id' field.")
            rule_type = rule_dict.get("rule_type")
            if not rule_type:
                raise PatchRuleEngineError("Rule must have a 'rule_type' field.")
            self.rules[rid] = dict(rule_dict)
            return

        final_id = rule_id if rule_id is not None else rule_or_id
        if not final_id or not isinstance(final_id, str):
            raise PatchRuleEngineError("Rule ID must be a non-empty string.")

        if pattern is None:
            raise PatchRuleEngineError("Rule pattern cannot be None.")

        rule_data = {
            "id": final_id,
            "pattern": pattern,
            "severity": severity,
            "rule_type": kwargs.get("rule_type", "forbidden_pattern"),
        }
        rule_data.update(kwargs)
        self.rules[final_id] = rule_data

    def get_rules(self) -> Dict[str, Dict[str, Any]]:
        return self.rules

    def clear_rules(self) -> None:
        self.rules.clear()
        self.threshold_rules.clear()

    def set_threshold_rule(
        self,
        metric_name: str,
        max_val: Optional[Union[int, float]] = None,
        min_val: Optional[Union[int, float]] = None,
    ) -> None:
        if not metric_name:
            raise PatchRuleEngineError("Metric name cannot be empty.")
        self.threshold_rules[metric_name] = {
            "max_val": max_val,
            "min_val": min_val,
        }

    def evaluate_telemetry(self, snapshot: Dict[str, Any]) -> bool:
        for metric, rule in self.threshold_rules.items():
            if metric in snapshot:
                val = snapshot[metric]
                max_v = rule.get("max_val")
                min_v = rule.get("min_val")
                if max_v is not None and val > max_v:
                    raise RuleViolationError(
                        f"Metric '{metric}' value {val} exceeded max threshold {max_v}"
                    )
                if min_v is not None and val < min_v:
                    raise RuleViolationError(
                        f"Metric '{metric}' value {val} below min threshold {min_v}"
                    )
        return True

    def validate_patch(self, patch_content: str) -> bool:
        for rid, rdata in self.rules.items():
            pattern = rdata.get("pattern")
            if pattern and re.search(pattern, patch_content):
                raise RuleViolationError(
                    f"Rule violation detected for rule '{rid}': pattern '{pattern}' matched."
                )
        return True

    def evaluate_patch(
        self,
        patch_content: str,
        patch_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        violations: List[Dict[str, Any]] = []

        added_lines_count = sum(
            1
            for line in patch_content.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        )

        for rid, rdata in self.rules.items():
            rule_type = rdata.get("rule_type", "forbidden_pattern")
            severity = rdata.get("severity", "ERROR")

            if rule_type == "forbidden_pattern":
                pattern = rdata.get("pattern", "")
                match = re.search(pattern, patch_content)
                if match:
                    matched_text = match.group(0)
                    detail_msg = (
                        f"Forbidden pattern '{pattern}' found in patch: '{matched_text}'"
                    )
                    violation = {
                        "rule_id": rid,
                        "severity": severity,
                        "details": detail_msg,
                    }
                    violations.append(violation)
                    if self.logger:
                        self.logger.log_anomaly(
                            anomaly_type="rule_violation",
                            severity=severity,
                            details={
                                "rule_id": rid,
                                "patch_id": patch_id,
                                "pattern": pattern,
                                "match": matched_text,
                                "message": detail_msg,
                            },
                        )

            elif rule_type == "max_added_lines":
                max_lines = rdata.get("threshold", 0)
                if added_lines_count > max_lines:
                    detail_msg = (
                        f"Added lines {added_lines_count} exceeded threshold {max_lines}"
                    )
                    violation = {
                        "rule_id": rid,
                        "severity": severity,
                        "details": detail_msg,
                    }
                    violations.append(violation)
                    if self.logger:
                        self.logger.log_anomaly(
                            anomaly_type="rule_violation",
                            severity=severity,
                            details={
                                "rule_id": rid,
                                "patch_id": patch_id,
                                "added_lines": added_lines_count,
                                "threshold": max_lines,
                                "message": detail_msg,
                            },
                        )

        is_valid = len(violations) == 0
        return {
            "patch_id": patch_id,
            "is_valid": is_valid,
            "violations": violations,
        }

    def load_rules_from_file(self, filepath: str) -> int:
        count = 0
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        if isinstance(content, bytes):
            content = content.decode("utf-8")

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                rid, pattern = line.split(":", 1)
                self.add_rule(rule_id=rid.strip(), pattern=pattern.strip())
                count += 1
        return count