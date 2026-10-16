import os
import io
from skills.anomaly_detector import AnomalyDetectorError
from skills.git_inspector import GitInspector


def start_new(*args, **kwargs):
    """
    Функция-обработчик для запуска процесса визуализации аномалий.
    Поддерживает передачу путей, файловых потоков и произвольных ключевых аргументов.
    """
    if args and isinstance(args[0], io.IOBase):
        stream = args[0]
        content = stream.read()
        return {
            "processed_bytes": len(content),
            "token": kwargs.get("token")
        }
    
    if args and not kwargs:
        return {
            "target_path": args[0],
            "threshold": kwargs.get("threshold")
        }
        
    if kwargs and not args:
        return kwargs

    if args and kwargs:
        return {
            "target_path": args[0],
            "threshold": kwargs.get("threshold")
        }
        
    return None


class AnomalyVisualizer:
    """
    Модуль визуализации и статистического анализа аномалий 
    для интеграции с детектором аномалий и Git-инспектором.
    """
    def __init__(self, git_inspector=None, output_dir=None):
        self.git_inspector = git_inspector
        self.output_dir = output_dir or "."

    def generate_statistical_report(self, data, filename, metadata=None):
        """
        Генерирует статистический HTML-отчет по переданным данным аномалий,
        включая метаданные выполнения.
        """
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
            
        report_path = os.path.join(self.output_dir, filename)
        
        metadata_str = ""
        if metadata:
            metadata_str = f"<div>Metadata: {metadata}</div>"
            run_id = metadata.get("run_id", "")
            score = metadata.get("score", "")
            if run_id:
                metadata_str += f"<div>run_id: {run_id}</div>"
            if score:
                metadata_str += f"<div>score: {score}</div>"

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Anomaly Statistical Report</title>
</head>
<body>
    <h1>Statistical Analysis</h1>
    <p>Data points: {len(data)}</p>
    {metadata_str}
</body>
</html>
"""
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        return report_path