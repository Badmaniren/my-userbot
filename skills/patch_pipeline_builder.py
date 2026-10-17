from skills.patch_evaluator import PatchEvaluator
from skills.patch_verifier import PatchVerifier

class PatchPipelineBuilderError(Exception):
    """Custom exception for PatchPipelineBuilder errors."""
    pass

class PipelineResult(dict):
    """Hybrid result container compatible with both dict-access and attribute-access."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__.update(kwargs)
        if "evaluation" in kwargs:
            eval_obj = kwargs["evaluation"]
            for attr in dir(eval_obj):
                if not attr.startswith('_'):
                    try:
                        setattr(self, attr, getattr(eval_obj, attr))
                    except AttributeError:
                        raise

    def __getattr__(self, name):
        if name in self:
            return self[name]
        raise AttributeError(f"'PipelineResult' object has no attribute '{name}'")


class PatchPipelineBuilder:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.evaluator = PatchEvaluator(repo_path=self.repo_path)
        self.verifier = PatchVerifier(repo_path=self.repo_path, inspector=None, executor=None)

    def run_pipeline(self, patch_content: str, target_file: str) -> PipelineResult:
        try:
            eval_result = self.evaluator.evaluate(
                patch_content,
                collect_telemetry=True,
                target_file=target_file
            )
        except Exception as e:
            raise PatchPipelineBuilderError(str(e))

        if not eval_result.is_safe:
            return PipelineResult({
                "success": False,
                "evaluation": eval_result,
                "verification": False,
                "is_safe": getattr(eval_result, "is_safe", False),
                "is_valid": getattr(eval_result, "is_valid", True)
            })

        # Интеграционный тест ожидает словарь с ключом "content", если PatchVerifier принимает словарь,
        # либо мы передаем строку, если верификатор ожидает строку. Судя по ошибке:
        # AttributeError: 'str' object has no attribute 'get' в patch_verifier.py на строке 129:
        # content = patch_data.get("content", "")
        # PatchVerifier ожидает словарь вида {"content": patch_content, "target_file": target_file} или аналогичный.
        # Передадим словарь, содержащий необходимые поля, обеспечивая совместимость с обоими интерфейсами.
        verifier_input = {"content": patch_content, "target_file": target_file}
        verification_result = self.verifier.verify_and_apply(verifier_input)

        success = bool(eval_result.is_safe and verification_result)

        return PipelineResult({
            "success": success,
            "evaluation": eval_result,
            "verification": verification_result,
            "is_safe": getattr(eval_result, "is_safe", True),
            "is_valid": getattr(eval_result, "is_valid", True)
        })

    def run_stream_pipeline(self, stream_data) -> PipelineResult:
        try:
            eval_result = self.evaluator.evaluate_stream(stream_data)
        except Exception as e:
            raise PatchPipelineBuilderError(str(e))

        if not eval_result.is_safe:
            return PipelineResult({
                "success": False,
                "evaluation": eval_result,
                "verification": False,
                "is_safe": getattr(eval_result, "is_safe", False),
                "is_valid": getattr(eval_result, "is_valid", True)
            })

        stream_data.seek(0)
        patch_content = stream_data.read().decode('utf-8')

        verifier_input = {"content": patch_content}
        verification_result = self.verifier.verify_and_apply(verifier_input)

        success = bool(eval_result.is_safe and verification_result)

        return PipelineResult({
            "success": success,
            "evaluation": eval_result,
            "verification": verification_result,
            "is_safe": getattr(eval_result, "is_safe", True),
            "is_valid": getattr(eval_result, "is_valid", True)
        })