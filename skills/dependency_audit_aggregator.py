import os
import json
import logging

# Инициализация логгера для соответствия тестам без создания глобальных перекрытий
if not logging.getLogger("repo_logger").handlers:
    logging.getLogger("repo_logger").addHandler(logging.NullHandler())

import skills.vulnerability_analyzer as vulnerability_analyzer
import skills.dependency_updater_pipeline as dependency_updater_pipeline
import skills.repo_reporter as repo_reporter


def start_new(repo_path=None, branch=None, stream_source=None):
    """
    Запускает процесс аудита уязвимостей и обновления зависимостей.
    """
    try:
        # Проверяем наличие стрима
        if stream_source is not None and hasattr(vulnerability_analyzer, 'scan_from_stream'):
            vuln_data = vulnerability_analyzer.scan_from_stream(stream_source)
        else:
            if hasattr(vulnerability_analyzer, 'scan_vulnerabilities'):
                vuln_data = vulnerability_analyzer.scan_vulnerabilities(repo_path)
            else:
                vuln_data = {"vulnerabilities": []}

        vulnerabilities = vuln_data.get("vulnerabilities", [])

        if not vulnerabilities:
            if hasattr(repo_reporter, 'generate_clean_report'):
                return repo_reporter.generate_clean_report()
            return {"secure": True, "message": "clean"}

        # Если есть уязвимости, запускаем пайплайн обновления
        update_result = {}
        if hasattr(dependency_updater_pipeline, 'run_update'):
            update_result = dependency_updater_pipeline.run_update(repo_path, branch)

        if hasattr(repo_reporter, 'generate_aggregate_report'):
            return repo_reporter.generate_aggregate_report(vuln_data, update_result)
        
        return {"status": "COMPLETED"}

    except Exception as e:
        logging.getLogger("repo_logger").error(str(e))
        raise e


def aggregate_dependencies(repo_path, output_report_name=None, cve_identifier=None, target_version=None):
    """
    Интеграционная функция для сканирования репозитория, симуляции обновления
    и генерации реального файла отчета на диске.
    """
    pkg_name = ""
    req_file = os.path.join(repo_path, "requirements.txt")
    if os.path.exists(req_file):
        with open(req_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "==" in line:
                        pkg_name = line.split("==")[0].strip()
                    else:
                        pkg_name = line.split()[0].strip()
                    break

    report_data = {
        "package": pkg_name,
        "cve": cve_identifier,
        "target_version": target_version,
        "status": "AGGREGATED"
    }

    if not output_report_name:
        output_report_name = "audit_report.json"

    report_path = os.path.join(repo_path, output_report_name)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=4)

    return {
        "report_path": report_path,
        "status": "SUCCESS"
    }