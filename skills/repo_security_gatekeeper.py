import os
import json
import io

from skills import repo_scanner
from skills import vulnerability_analyzer
from skills import repo_logger
from skills import vulnerability_security_gate
from skills import repo_notifier
from skills import repo_ci_pipeline
from skills import dependency_audit_pipeline
from skills import repo_recovery
from skills import repo_auditor


class RepoSecurityGatekeeper:
    def __init__(self, logger=None, auditor=None, analyzer=None):
        self.logger = logger or repo_logger
        self.auditor = auditor or repo_auditor
        self.analyzer = analyzer or vulnerability_analyzer

    def evaluate_repository(self, audit_config):
        run_id = audit_config.get("run_id", "default")
        scan_target = audit_config.get("scan_target", ".")
        
        vulnerabilities = []
        if os.path.exists(scan_target):
            for root, dirs, files in os.walk(scan_target):
                for file in files:
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        if "SECRET_KEY" in content:
                            vulnerabilities.append({"file": file_path, "type": "Hardcoded Secret"})

        result = {
            "status": "vulnerable" if vulnerabilities else "clean",
            "vulnerabilities_detected": len(vulnerabilities),
            "vulnerabilities": vulnerabilities,
            "report_generated": True
        }

        report_artifact_path = os.path.join(scan_target, f"security_gate_report_{run_id}.json")
        with open(report_artifact_path, "w", encoding="utf-8") as f:
            json.dump(result, f)

        return result


def start_new(repo, branch=None, remote_url=None, fail_fast=False, run_ci=False, auto_recover=False):
    if auto_recover:
        try:
            stream = repo_scanner(repo)
            content = stream.read()
        except ConnectionError as e:
            code = 500
            for part in str(e).split():
                if part.isdigit() and len(part) == 3:
                    code = int(part)
            recovery_res = repo_recovery.restore()
            recovery_res["code"] = code
            return recovery_res

    if fail_fast:
        stream = repo_scanner(repo)
        content = stream.read()
        vulnerability_security_gate.evaluate(content)

    if run_ci:
        pipeline_res = repo_ci_pipeline.run()
        dependency_audit_pipeline.execute()
        return pipeline_res

    stream = repo_scanner(repo)
    _ = stream.read()

    repo_logger.info(f"Starting scan for repo {repo}")
    analysis_res = vulnerability_analyzer.analyze(repo)
    if isinstance(analysis_res, dict):
        analysis_res.setdefault("target", repo)
        analysis_res.setdefault("status", "clean")
        return analysis_res
    
    return {"status": "clean", "target": repo}