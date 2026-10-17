from skills.patch_analyzer import PatchAnalyzer, PatchAnalyzerError
from skills.patch_verifier import PatchVerifier


class PatchSafeExecutorError(Exception):
    """Исключение, выбрасываемое при ошибках безопасного выполнения патча."""
    pass


class PatchSafeExecutor:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.analyzer = PatchAnalyzer()
        self.verifier = PatchVerifier(repo_path)

    def execute(self, patch_data: dict) -> bool:
        diff = patch_data.get("diff", "")
        
        try:
            analysis = self.analyzer.analyze(diff)
        except PatchAnalyzerError as e:
            raise PatchSafeExecutorError(str(e))

        if analysis.get("status") == "unsafe":
            risks = analysis.get("risks", [])
            risk_msg = ", ".join(risks) if risks else "Unknown risks detected"
            raise PatchSafeExecutorError(f"Unsafe patch detected: {risk_msg}")

        result = self.verifier.verify_and_apply(patch_data)
        return result

    def execute_stream(self, stream) -> bool:
        analysis = self.analyzer.analyze_stream(stream)
        
        if analysis.get("status") == "unsafe":
            risks = analysis.get("risks", [])
            risk_msg = ", ".join(risks) if risks else "Unknown risks detected"
            raise PatchSafeExecutorError(f"Unsafe patch detected: {risk_msg}")

        if hasattr(stream, "seek"):
            stream.seek(0)
        diff_content = stream.read()
        if isinstance(diff_content, bytes):
            diff_content = diff_content.decode('utf-8')

        patch_data = {
            "diff": diff_content,
            "target": "",
            "checksum": ""
        }

        result = self.verifier.verify_and_apply(patch_data)
        return result

    def execute_safe_patch(self, diff_text: str, target_path: str) -> bool:
        patch_data = {
            "diff": diff_text,
            "target": target_path,
            "checksum": ""
        }
        return self.execute(patch_data)