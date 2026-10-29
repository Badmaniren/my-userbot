from skills import patch_sanitizer
from skills import patch_checker
from skills import patch_applier


class PatchPipelineError(Exception):
    """Исключение, возникающее при ошибках в пайплайне обработки патчей."""
    pass


class PatchPipelineOrchestrator:
    def __init__(self, repo_path: str, policy: str = "strict", backup_tag: str = "backup"):
        self.repo_path = repo_path
        self.policy = policy
        self.backup_tag = backup_tag

        self.sanitizer = patch_sanitizer.PatchSanitizer()
        self.checker = patch_checker.PatchChecker()
        self.applier = patch_applier.PatchApplier(repo_path=self.repo_path)

    def process_patch(self, patch_path: str, target_file: str) -> bool:
        with open(patch_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()

        return self.process_and_apply(raw_content, target_file)

    def process_and_apply(self, patch_source, target_file: str) -> bool:
        sanitized_content = self.sanitizer.sanitize(patch_source)

        check_res = self.checker.check(sanitized_content, self.repo_path, target_file, self.policy)
        if isinstance(check_res, dict):
            if check_res.get("status") == "failed":
                reason = check_res.get("reason", "Unknown check failure")
                raise PatchPipelineError(f"Patch check failed: {reason}")
            if check_res.get("is_safe") is False or check_res.get("is_valid") is False:
                reasons = check_res.get("evaluation", {}).get("reasons") or check_res.get("policy_verdict") or "Invalid or unsafe patch"
                raise PatchPipelineError(f"Patch check failed: {reasons}")
            if check_res.get("policy_verdict", {}).get("disallowed_risks"):
                reason = check_res["policy_verdict"]["disallowed_risks"]
                raise PatchPipelineError(f"Patch check failed: {reason}")

        try:
            if not self.applier.create_recovery_point(self.backup_tag):
                raise PatchPipelineError("Failed to create recovery point")
        except PatchPipelineError:
            raise
        except Exception as e:
            raise PatchPipelineError(f"Failed to create recovery point: {e}") from e

        try:
            applied = self.applier.apply_patch(sanitized_content)
            if not applied:
                self.applier.rollback(self.backup_tag)
                raise PatchPipelineError("Failed to apply patch")
        except PatchPipelineError:
            raise
        except Exception as e:
            try:
                self.applier.rollback(self.backup_tag)
            except Exception:
                pass
            raise PatchPipelineError(f"Failed to apply patch: {e}") from e

        try:
            verified = self.applier.verify_repository_state()
            if not verified:
                self.applier.rollback(self.backup_tag)
                raise PatchPipelineError("Repository state verification failed")
        except PatchPipelineError:
            raise
        except Exception as e:
            try:
                self.applier.rollback(self.backup_tag)
            except Exception:
                pass
            raise PatchPipelineError(f"Repository state verification failed: {e}") from e

        return True