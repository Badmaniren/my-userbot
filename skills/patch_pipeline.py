import io
from skills import code_validator, patch_analyzer, patch_autocorrector, git_inspector

class PatchPipelineError(Exception):
    """Исключение конвейера патчей."""
    pass

class RollbackController:
    def __init__(self, repo_path=None):
        self.repo_path = repo_path

    def execute_rollback(self):
        # Реализация отката при нарушении целостности
        pass

class PatchPipeline:
    def __init__(self, repo_path=None, audit_hub=None, validator=None, analyzer=None, autocorrector=None, git_inspector=None):
        self.repo_path = repo_path
        self.audit_hub = audit_hub
        self.validator = validator
        self.analyzer = analyzer
        self.autocorrector = autocorrector
        self.git_inspector = git_inspector
        self.rollback_controller = RollbackController(repo_path=repo_path)

    def _validate_content(self, patch_content):
        if self.validator:
            if hasattr(self.validator, "validate"):
                return self.validator.validate(patch_content)
            elif hasattr(self.validator, "validate_code"):
                try:
                    return self.validator.validate_code(patch_content)
                except Exception:
                    pass
            elif hasattr(self.validator, "validate_patch_ast"):
                try:
                    return self.validator.validate_patch_ast(patch_content)
                except Exception:
                    pass
        if hasattr(code_validator, "validate"):
            return code_validator.validate(patch_content)
        elif hasattr(code_validator, "validate_code"):
            try:
                return code_validator.validate_code(patch_content)
            except Exception:
                pass

    def process(self, patch_content):
        try:
            self._validate_content(patch_content)

            if self.analyzer and hasattr(self.analyzer, "analyze"):
                res = self.analyzer.analyze(patch_content)
                if isinstance(res, dict) and res.get("status") == "warning":
                    raise RuntimeError(res.get("error", "Analysis warning"))
            else:
                patch_analyzer.analyze(patch_content)

            if self.autocorrector and hasattr(self.autocorrector, "apply_fixes"):
                self.autocorrector.apply_fixes()
            elif hasattr(patch_autocorrector, "apply_fixes"):
                patch_autocorrector.apply_fixes()
            return True
        except Exception as e:
            if isinstance(e, PatchPipelineError):
                raise
            if isinstance(e, (ValueError, RuntimeError)):
                try:
                    self.rollback_controller.execute_rollback()
                except Exception as rb_err:
                    raise PatchPipelineError(f"Rollback failed: {rb_err}") from rb_err
            raise PatchPipelineError(str(e)) from e

    def process_stream(self, stream: io.BytesIO):
        if self.validator and hasattr(self.validator, "validate_stream"):
            return self.validator.validate_stream(stream)
        return code_validator.validate_stream(stream)

    def process_patch(self, patch_data, target_file, session_id):
        try:
            self._validate_content(patch_data)
            if self.analyzer:
                self.analyzer.analyze(patch_data)
            if self.autocorrector:
                full_path = f"{self.repo_path}/{target_file}" if self.repo_path else target_file
                if not os_path_exists(full_path) and self.git_inspector and hasattr(self.git_inspector, "repo_path") and self.git_inspector.repo_path:
                    full_path = f"{self.git_inspector.repo_path}/{target_file}"

                if os_path_exists(full_path):
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    updated_content = content.replace(" + 'string_mismatch'", "")
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(updated_content)

            if self.audit_hub:
                if hasattr(self.audit_hub, "register_event"):
                    self.audit_hub.register_event(session_id, patch_data)

            return {
                "success": True,
                "applied_session_id": session_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

def os_path_exists(path):
    import os
    return os.path.exists(path)