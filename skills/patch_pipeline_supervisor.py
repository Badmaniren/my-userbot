from skills.patch_analyzer import PatchAnalyzer, PatchAnalyzerError
from skills.patch_verifier import PatchVerifier, PatchExecutorError, PatchVerifierError


class PatchPipelineSupervisorError(Exception):
    """Исключение конвейера обработки патчей."""
    pass


class PatchPipelineSupervisor:
    """Модуль управления конвейером патчей."""

    def __init__(self, repo_path=None, analyzer=None, verifier=None):
        self.repo_path = repo_path or "."
        self.analyzer = analyzer if analyzer is not None else PatchAnalyzer()
        self.verifier = verifier if verifier is not None else PatchVerifier(repo_path=self.repo_path)

    def run_pipeline(self, patch_data: dict) -> bool:
        """Запуск стандартного конвейера анализа и верификации патча."""
        try:
            diff_text = patch_data.get("diff") if isinstance(patch_data, dict) else str(patch_data)
            analysis = self.analyzer.analyze(diff_text)
            if isinstance(analysis, dict) and not analysis.get("is_valid", True):
                errors = analysis.get("errors", ["Invalid patch structure"])
                raise PatchPipelineSupervisorError(f"Patch analysis failed: {errors}")
        except PatchAnalyzerError as e:
            raise PatchPipelineSupervisorError(str(e)) from e

        try:
            result = self.verifier.verify_and_apply(patch_data)
        except (PatchExecutorError, PatchVerifierError) as e:
            raise PatchPipelineSupervisorError(str(e)) from e
        except Exception as e:
            raise PatchPipelineSupervisorError(f"Verification failed: {e}") from e

        return result

    def run_stream_pipeline(self, stream, patch_data: dict) -> bool:
        """Запуск потокового конвейера анализа и верификации патча."""
        try:
            analysis = self.analyzer.analyze_stream(stream)
            if isinstance(analysis, dict) and not analysis.get("is_valid", True):
                errors = analysis.get("errors", ["Invalid stream patch structure"])
                raise PatchPipelineSupervisorError(f"Stream analysis failed: {errors}")
        except PatchAnalyzerError as e:
            raise PatchPipelineSupervisorError(str(e)) from e

        try:
            result = self.verifier.verify_and_apply(patch_data)
        except (PatchExecutorError, PatchVerifierError) as e:
            raise PatchPipelineSupervisorError(str(e)) from e
        except Exception as e:
            raise PatchPipelineSupervisorError(f"Verification failed: {e}") from e

        return result

    def process_patch(self, diff_text: str, session_id: str, target_file: str) -> dict:
        """Сквозная обработка патча для интеграционного теста."""
        try:
            analysis_result = self.analyzer.analyze(diff_text)
            if isinstance(analysis_result, dict) and not analysis_result.get("is_valid", True):
                errors = analysis_result.get("errors", ["Invalid patch structure"])
                raise PatchPipelineSupervisorError(f"Patch analysis failed: {errors}")
        except PatchAnalyzerError as e:
            raise PatchPipelineSupervisorError(str(e)) from e

        patch_data = {
            "id": session_id,
            "diff": diff_text,
            "target": target_file
        }

        try:
            verification_result = self.verifier.verify_and_apply(patch_data)
        except (PatchExecutorError, PatchVerifierError) as e:
            raise PatchPipelineSupervisorError(str(e)) from e
        except Exception as e:
            raise PatchPipelineSupervisorError(f"Verification failed: {e}") from e

        stats = (
            analysis_result.get("statistics")
            if isinstance(analysis_result, dict) and "statistics" in analysis_result
            else analysis_result
        )

        return {
            "analyzed": True,
            "verified": verification_result,
            "session_id": session_id,
            "statistics": stats
        }