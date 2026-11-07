import json
import requests

try:
    from skills.repo_auditor import repo_auditor
except ImportError:
    repo_auditor = None

from skills.vulnerability_analyzer import vulnerability_analyzer

try:
    from skills.repo_reporter import repo_reporter
except ImportError:
    repo_reporter = None


def start_new(repo_url, api_token=None, output_path=None):
    headers = {}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"

    try:
        response = requests.post(
            "https://api.github.com/v1/security/scan",
            json={"repository": repo_url},
            headers=headers,
            timeout=30
        )
        
        try:
            data = response.json()
        except (ValueError, json.JSONDecodeError) as e:
            return {
                "error": "Invalid JSON response",
                "status_code": response.status_code
            }

        if response.status_code >= 400:
            return {
                "error": "Request failed",
                "status_code": response.status_code,
                "data": data
            }

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f)

        return data

    except requests.exceptions.ConnectionError as e:
        raise Exception(f"Connection error: {e}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error: {e}")


def repo_security_scanner(payload):
    scan_uuid = payload.get("scan_uuid")
    path = payload.get("path")
    severity = payload.get("severity", "MEDIUM")

    vulnerabilities = []
    
    if vulnerability_analyzer:
        vuln_res = vulnerability_analyzer(target_path=path, threshold=severity)
        if isinstance(vuln_res, dict):
            vulnerabilities.append(vuln_res)

    return {
        "status": "success",
        "scan_uuid": scan_uuid,
        "path": path,
        "vulnerabilities": vulnerabilities
    }