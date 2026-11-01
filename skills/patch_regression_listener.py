import uuid
import os
from skills.git_inspector import GitInspector

class PatchRegressionListenerError(Exception):
    """Исключение для ошибок прослушивателя регрессии патчей."""
    pass

class PatchRegressionListener:
    def __init__(self, watch_dir, callback=None):
        self.watch_dir = watch_dir
        self.callback = callback
        self.is_running = False

    def start_listening(self):
        self.is_running = True
        return True

    def stop_listening(self):
        self.is_running = False
        return False

    def trigger_regression(self, patch_data):
        if not patch_data:
            raise PatchRegressionListenerError("Empty patch data")
        if self.callback:
            return self.callback(patch_data)
        return True

def listen_for_patches(target_path):
    return [uuid.uuid4().hex, target_path]

def start_regression_listening(listener_payload):
    patch_id = listener_payload.get("patch_id")
    repo_path = listener_payload.get("repo_path")
    log_path = listener_payload.get("log_path")
    file_target = listener_payload.get("file_target")

    if log_path:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"Processed patch {patch_id} for repo {repo_path}\n")

    return {
        "status": "success",
        "patch_id": patch_id,
        "file_target": file_target
    }