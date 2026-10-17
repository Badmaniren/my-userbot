from skills.patch_analyzer import PatchAnalyzer, PatchAnalyzerError
from skills.patch_verifier import PatchVerifier, PatchExecutorError


class PatchPipelineSupervisorError(Exception):
    """Исключение конвейера обработки патчей."""
    pass


class PatchPipelineSupervisor:
    """Модуль управления конвейером патчей."""

    def __init__(self, repo_path=None, analyzer=None, verifier=None):
        self.repo_path = repo_path
        self.analyzer = analyzer if analyzer is not None else PatchAnalyzer()
        self.verifier = verifier if verifier is not None else PatchVerifier(repo_path=self.repo_path)

    def run_pipeline(self, patch_data: dict) -> bool:
        """Запуск стандартного конвейера анализа и верификации патча."""
        try:
            diff_text = patch_data.get("diff")
            self.analyzer.analyze(diff_text)
        except PatchAnalyzerError as e:
            raise PatchPipelineSupervisorError(str(e)) from e

        try:
            result = self.verifier.verify_and_apply(patch_data)
        except PatchExecutorError as e:
            raise PatchPipelineSupervisorError(str(e)) from e

        return result

    def run_stream_pipeline(self, stream, patch_data: dict) -> bool:
        """Запуск потокового конвейера анализа и верификации патча."""
        try:
            self.analyzer.analyze_stream(stream)
        except PatchAnalyzerError as e:
            raise PatchPipelineSupervisorError(str(e)) from e

        try:
            result = self.verifier.verify_and_apply(patch_data)
        except PatchExecutorError as e:
            raise PatchPipelineSupervisorError(str(e)) from e

        return result

    def process_patch(self, diff_text: str, session_id: str, target_file: str) -> dict:
        """Сквозная обработка патча для интеграционного теста."""
        analysis_result = self.analyzer.analyze(diff_text)
        
        patch_data = {
            "id": session_id,
            "diff": diff_text,
            "target": target_file
        }
        
        verification_result = self.verifier.verify_and_apply(patch_data)

        return {
            "analyzed": True,
            "verified": verification_result,
            "session_id": session_id,
            "statistics": analysis_result
        }