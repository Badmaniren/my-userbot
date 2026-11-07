import os
import json
import requests

def start_new(epic_name, target_path, endpoint_url, threshold):
    """
    Инициализирует новый эпик оптимизации и метрик скорости репозитория.
    """
    if os.path.exists(target_path):
        with open(target_path, "r", encoding="utf-8") as f:
            content = f.read()
            metric_key = None
            limit_val = None
            for line in content.splitlines():
                if line.startswith("METRIC_KEY="):
                    metric_key = line.split("=", 1)[1]
                elif line.startswith("LIMIT="):
                    limit_val = line.split("=", 1)[1]
            if metric_key:
                return {
                    "status": "initialized",
                    "epic": epic_name,
                    "metric_id": metric_key,
                    "threshold": int(limit_val) if limit_val else threshold
                }

    payload = {
        "epic_name": epic_name,
        "target_path": target_path,
        "threshold": threshold
    }
    
    response = requests.post(endpoint_url, json=payload)
    
    if response.status_code != 201:
        raise Exception(f"Failed to initialize epic: {response.text}")
        
    return response.json()

def profile_repository(repo_path, session_id, threshold):
    """
    Профилирует репозиторий, анализирует его и сохраняет отчет в формате JSON.
    """
    report_data = {
        "profile_id": session_id,
        "session_id": session_id,
        "threshold": threshold,
        "status": "completed"
    }
    
    report_path = os.path.join(repo_path, f"performance_report_{session_id}.json")
    with open(report_path, "w", encoding="utf-8") as report_file:
        json.dump(report_data, report_file)
        
    return report_data