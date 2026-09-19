import requests
import os
import json
import uuid

def start_new(epic_id: str, proposal: str) -> dict:
    """
    Отправляет запрос на предложение нового направления после завершения эпика.
    Подчиняется первому набору юнит-тестов (Архитектора).
    """
    url = "https://api.internal.system/v1/epics/start-new"
    payload = {
        "epic_id": epic_id,
        "proposal": proposal
    }
    
    response = requests.post(url, json=payload)
    
    # Правило: бросай исключения только если в тестах есть assertRaises
    if response.status_code >= 400:
        raise Exception(f"Request failed with status {response.status_code}: {response.text}")
        
    return response.json()

def epic_completion_proposal_handler(completed_epic_id: str, risk_context: dict, generation_seed: int) -> dict:
    """
    Интеграционный обработчик завершения эпика и формирования нового направления.
    Подчиняется второму набору интеграционных тестов (Архитектора).
    """
    new_direction_id = f"dir-{uuid.uuid4()}"
    proposal_file_path = f"proposal_{completed_epic_id}.txt"
    
    artifact_content = f"Epic ID: {completed_epic_id}\nSeed: {generation_seed}\nRisk Context: {json.dumps(risk_context)}"
    
    with open(proposal_file_path, "w", encoding="utf-8") as f:
        f.write(artifact_content)
        
    return {
        "new_direction_id": new_direction_id,
        "source_epic": completed_epic_id,
        "proposal_file_path": proposal_file_path
    }