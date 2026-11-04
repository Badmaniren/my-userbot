import os
import json

class RepoAuditor:
    """Модуль аудита репозитория для оценки структуры кода, расчета метрик и обнаружения потенциальных проблем."""
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def audit(self):
        """Проведение общего аудита репозитория."""
        metrics = self.calculate_metrics()
        issues = self.detect_issues()
        structure = self.analyze_structure()
        return {
            "metrics": metrics,
            "issues": issues,
            "structure": structure
        }

    def audit_repository(self):
        """Алиас для аудита репозитория."""
        return self.audit()

    def run(self):
        """Запуск аудита репозитория."""
        return self.audit()

    def calculate_metrics(self) -> dict:
        """Расчет метрик кода по файлам в репозитории."""
        metrics = {}
        if not os.path.exists(self.repo_path):
            return metrics

        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        metrics[file] = {
                            "lines_count": len(lines),
                            "comment_lines": sum(1 for line in lines if line.strip().startswith("#"))
                        }
        return metrics

    def detect_issues(self) -> list:
        """Обнаружение потенциальных проблем и маркеров в коде."""
        issues = []
        if not os.path.exists(self.repo_path):
            return issues

        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        for idx, line in enumerate(f, 1):
                            if "TODO" in line or "FIX" in line or len(line.strip()) > 200:
                                issues.append({
                                    "file": file_path,
                                    "line": idx,
                                    "content": line.strip()
                                })
        return issues

    def analyze_structure(self) -> dict:
        """Анализ структуры директорий и файлов репозитория."""
        structure = {"directories": [], "files": []}
        if not os.path.exists(self.repo_path):
            return structure

        for root, dirs, files in os.walk(self.repo_path):
            for d in dirs:
                structure["directories"].append(os.path.join(root, d))
            for f in files:
                structure["files"].append(os.path.join(root, f))
        return structure

    def evaluate_structure(self) -> dict:
        return self.analyze_structure()

    def check_structure(self) -> dict:
        return self.analyze_structure()

    def generate_report(self, output_path: str = None):
        """Генерация и сохранение отчета об аудитории."""
        report_data = {
            "metrics": self.calculate_metrics(),
            "issues": self.detect_issues(),
            "structure": self.analyze_structure()
        }
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=4)
        return report_data

    def save_report(self, output_path: str = None):
        return self.generate_report(output_path)

    def process_log_stream(self, stream) -> str:
        """Обработка потока данных логов."""
        if hasattr(stream, "read"):
            data = stream.read()
            if isinstance(data, bytes):
                return data.decode("utf-8", errors="ignore")
            return str(data)
        return str(stream)

    def process_stream(self, stream) -> str:
        return self.process_log_stream(stream)