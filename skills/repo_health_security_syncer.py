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
            sync_id = metric_payload.get("sync_id", str(uuid.uuid4()))
            token = metric_payload.get("token")
            env_token = os.environ.get("REPO_SYNC_TOKEN")
            
            success = True
            if token and env_token and token != env_token:
                success = False

            health_score = metric_payload.get("health_score")
            vulnerabilities = metric_payload.get("vulnerabilities")

            result = {
                "success": success,
                "synced_id": sync_id,
                "health_data": {"health_score": health_score},
                "security_data": {"vulnerabilities": vulnerabilities, "token": token, "security_score": metric_payload.get("security_score")}
            }

            if self.target_directory:
                expected_file_name = f"audit_{sync_id}.json"
                expected_file_path = os.path.join(self.target_directory, expected_file_name)
                
                audit_content = {
                    "audit_id": str(uuid.uuid4()),
                    "correlation_id": sync_id,
                    "health_metrics": {"health_score": health_score},
                    "security_metrics": {"vulnerabilities": vulnerabilities}
                }
                
                os.makedirs(self.target_directory, exist_ok=True)
                with open(expected_file_path, "w", encoding="utf-8") as f:
                    json.dump(audit_content, f)

            return result

        try:
            health_resp = requests.get(self.health_url, timeout=10)
            if health_resp.status_code != 200:
                return {
                    "success": False,
                    "error": f"Health check failed with status {health_resp.status_code}: {health_resp.text}",
                    "status_code": health_resp.status_code
                }
            health_data = health_resp.json()

            security_resp = requests.get(self.security_url, timeout=10)
            if security_resp.status_code != 200:
                return {
                    "success": False,
                    "error": f"Security check failed with status {security_resp.status_code}: {security_resp.text}",
                    "status_code": security_resp.status_code
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
                "error": str(e),
                "status_code": 500
            }

    def export_audit_stream(self):
        resp = requests.get(self.health_url, timeout=10)
        raw_stream = getattr(resp, "raw", None)
        
        content = b""
        if raw_stream and hasattr(raw_stream, "read"):
            content = raw_stream.read()
        elif hasattr(resp, "content"):
            content = resp.content

        stream_hash = hashlib.sha256(content).hexdigest()
        bytes_read = len(content)

        return {
            "stream_hash": stream_hash,
            "bytes_read": bytes_read
        }