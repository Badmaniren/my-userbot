import os
import uuid
import hashlib
import requests
import json

class RepoHealthSecuritySyncer:
    def __init__(self, repo_id=None, health_url=None, security_url=None, target_directory=None):
        self.repo_id = repo_id
        self.health_url = health_url
        self.security_url = security_url
        self.target_directory = target_directory

    def synchronize(self, metric_payload=None):
        if metric_payload is not None:
            sync_id = metric_payload.get("sync_id")
            token = metric_payload.get("token")
            expected_token = os.environ.get("REPO_SYNC_TOKEN")
            
            if expected_token and token != expected_token:
                return {
                    "success": False,
                    "synced_id": sync_id
                }

            health_score = metric_payload.get("health_score")
            vulnerabilities = metric_payload.get("vulnerabilities")
            security_score = metric_payload.get("security_score")

            health_data = {"health_score": health_score}
            security_data = {
                "vulnerabilities": vulnerabilities,
                "token": token,
                "security_score": security_score
            }

            if self.target_directory:
                os.makedirs(self.target_directory, exist_ok=True)
                file_path = os.path.join(self.target_directory, f"audit_{sync_id}.json")
                file_content = {
                    "correlation_id": sync_id,
                    "health_metrics": health_data,
                    "security_metrics": security_data
                }
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(file_content, f)

            return {
                "success": True,
                "synced_id": sync_id,
                "health_data": health_data,
                "security_data": security_data
            }
        else:
            try:
                health_resp = requests.get(self.health_url)
                if health_resp.status_code != 200:
                    return {
                        "success": False,
                        "status_code": health_resp.status_code,
                        "error": health_resp.text
                    }
                health_data = health_resp.json()

                sec_resp = requests.get(self.security_url)
                if sec_resp.status_code != 200:
                    return {
                        "success": False,
                        "status_code": sec_resp.status_code,
                        "error": sec_resp.text
                    }
                security_data = sec_resp.json()

                return {
                    "success": True,
                    "health_data": health_data,
                    "security_data": security_data
                }
            except Exception as e:
                return {
                    "success": False,
                    "status_code": 500,
                    "error": str(e)
                }

    def export_audit_stream(self):
        resp = requests.get(self.health_url)
        if hasattr(resp, "raw") and resp.raw:
            content = resp.raw.read()
        else:
            content = resp.content

        stream_hash = hashlib.sha256(content).hexdigest()
        return {
            "stream_hash": stream_hash,
            "bytes_read": len(content)
        }