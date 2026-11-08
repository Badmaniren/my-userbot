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
        env_token = os.environ.get("REPO_SYNC_TOKEN")

        if metric_payload is not None:
            sync_id = metric_payload.get("sync_id") or uuid.uuid4().hex
            token = metric_payload.get("token")

            if env_token is not None and token != env_token:
                return {"success": False, "synced_id": sync_id}

            health_score = metric_payload.get("health_score")
            vulnerabilities = metric_payload.get("vulnerabilities")
            security_score = metric_payload.get("security_score")

            health_data = {"health_score": health_score}
            if token is not None:
                health_data["token"] = token

            security_data = {
                "vulnerabilities": vulnerabilities,
                "security_score": security_score
            }
            if token is not None:
                security_data["token"] = token

            if self.target_directory:
                if not os.path.exists(self.target_directory):
                    os.makedirs(self.target_directory, exist_ok=True)
                expected_file = os.path.join(self.target_directory, f"audit_{sync_id}.json")
                audit_data = {
                    "correlation_id": sync_id,
                    "health_metrics": {"health_score": health_score},
                    "security_metrics": {
                        "security_score": security_score,
                        "vulnerabilities": vulnerabilities
                    }
                }
                with open(expected_file, "w", encoding="utf-8") as f:
                    json.dump(audit_data, f)

            return {
                "success": True,
                "synced_id": sync_id,
                "health_data": health_data,
                "security_data": security_data
            }

        try:
            health_resp = requests.get(self.health_url)
            if health_resp.status_code != 200:
                return {
                    "success": False,
                    "status_code": health_resp.status_code,
                    "error": getattr(health_resp, "text", "")
                }
            health_data = health_resp.json()

            security_resp = requests.get(self.security_url)
            if security_resp.status_code != 200:
                return {
                    "success": False,
                    "status_code": security_resp.status_code,
                    "error": getattr(security_resp, "text", "")
                }
            security_data = security_resp.json()

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
        if getattr(resp, "raw", None) is not None and hasattr(resp.raw, "read"):
            content = resp.raw.read()
        else:
            content = getattr(resp, "content", b"")

        stream_hash = hashlib.sha256(content).hexdigest()
        bytes_read = len(content)

        return {
            "stream_hash": stream_hash,
            "bytes_read": bytes_read
        }