import json

class RepoHealthTransformationError(Exception):
    """Исключение при ошибке трансформации метрик здоровья репозитория."""
    pass

class RepoHealthAnalyticsэффициентTransformer:
    def transform(self, data: dict) -> dict:
        if not isinstance(data, dict) or ("repository_id" not in data and "repo_uuid" not in data):
            raise RepoHealthTransformationError("Invalid data format for transformation.")
        
        # Поддержка интеграционного формата
        if "normalized_score" in data or "health_score" in data or "metrics_summary" in data:
            return data

        repo_id = data.get("repository_id") or data.get("repo_uuid")
        metrics = data.get("metrics", {})
        
        normalized_metrics = {}
        for metric_name, metric_info in metrics.items():
            if isinstance(metric_info, dict):
                normalized_metrics[metric_name] = {
                    "value": metric_info.get("score"),
                    "severity": metric_info.get("status")
                }
                
        return {
            "repo_uuid": repo_id,
            "normalized_metrics": normalized_metrics
        }

    def transform_stream(self, stream) -> dict:
        data = json.load(stream)
        return self.transform(data)

def transform_health_metrics(payload: dict) -> dict:
    transformer = RepoHealthAnalyticsэффициентTransformer()
    return transformer.transform(payload)

def repo_health_analytics_transformer(validated_data):
    # Интеграционная функция для работы с валидатором
    if not isinstance(validated_data, dict):
        raise RepoHealthTransformationError("Validated data must be a dictionary.")
    
    repo_id = validated_data.get("repository_id") or validated_data.get("repo_uuid")
    health_score = validated_data.get("health_score")
    open_issues = validated_data.get("open_issues")
    
    return {
        "repository_id": repo_id,
        "normalized_score": health_score,
        "metrics_summary": {
            "open_issues": open_issues
        },
        "transformed_at": True
    }