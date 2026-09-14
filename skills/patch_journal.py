import os
import json
import time
from typing import Dict, Any, List, Optional, Union

from skills.error_recovery_hub import ErrorRecoveryHub
from skills.auto_patch_pipeline import AutoPatchPipeline

class JournalEntry:
    def __init__(
        self,
        success: bool,
        incident_id: str,
        module_name: str,
        error: str,
        patch_data: str,
        timestamp: Optional[float] = None
    ):
        self.success = success
        self.incident_id = incident_id
        self.module_name = module_name
        self.error = error
        self.patch_data = patch_data
        self.timestamp = timestamp if timestamp is not None else time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "incident_id": self.incident_id,
            "module_name": self.module_name,
            "error": self.error,
            "patch_data": self.patch_data,
            "timestamp": self.timestamp
        }


class PatchJournal:
    def __init__(self, storage_path: str = "patch_journal.jsonl"):
        self.storage_path = storage_path

    def _append_record(self, data: Dict[str, Any]) -> None:
        dirname = os.path.dirname(os.path.abspath(self.storage_path))
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(self.storage_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

    def log_event(
        self,
        success: bool,
        incident_id: str,
        module_name: str,
        error: str,
        patch_data: str
    ) -> None:
        entry = JournalEntry(
            success=success,
            incident_id=incident_id,
            module_name=module_name,
            error=error,
            patch_data=patch_data
        )
        self._append_record(entry.to_dict())

    def get_all(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.storage_path):
            return []
        records = []
        with open(self.storage_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return records

    def get_records(self, module_name: Optional[str] = None) -> List[Dict[str, Any]]:
        all_records = self.get_all()
        if module_name is None:
            return all_records
        return [r for r in all_records if r.get("module_name") == module_name]

    def get_history(self, module_name: str) -> List[Dict[str, Any]]:
        return self.get_records(module_name=module_name)

    def get_incident_logs(self, incident_id: str) -> Optional[Dict[str, Any]]:
        all_records = self.get_all()
        for record in all_records:
            if record.get("incident_id") == incident_id:
                return record
        return None


class JournalStreamVerifier:
    def verify_stream(self, stream: Any) -> Dict[str, Any]:
        if hasattr(stream, "read"):
            content = stream.read()
            if isinstance(content, bytes):
                try:
                    content_str = content.decode('utf-8')
                except Exception:
                    content_str = str(content)
                size = len(content)
            elif isinstance(content, str):
                size = len(content.encode('utf-8'))
            else:
                size = len(str(content).encode('utf-8'))
            return {"valid": True, "size": size}
        elif isinstance(stream, (list, dict)):
            serialized = json.dumps(stream, ensure_ascii=False)
            return {"valid": True, "size": len(serialized.encode('utf-8'))}
        else:
            content_str = str(stream)
            return {"valid": True, "size": len(content_str.encode('utf-8'))}
