# Текущий эпик Унги

## Безопасный пайплайн исправления патчей: Санитизация → Проверка → Применение

- patch_sanitizer: Создаем первый модуль нового эпика для первичной очистки и нормализации патчей.
- patch_checker: Рефакторинг модуля patch_checker для успешного прохождения тестов и продвижения по эпику санитизации и проверки патчей.
- patch_analyzer: Stabilizing the analyzer is the critical bridge between sanitization and verification; without a robust analyzer, the pipeline cannot reliably pass the patch to the validator.
- patch_evaluator: Исправление и стабилизация patch_evaluator для завершения шага оценки в безопасном пайплайне патчей.
- patch_verifier: Рефакторинг patch_verifier для прохождения всех провальных тестов и замыкания этапа проверки в конвейере.
- patch_analyzer: Создание отсутствующего модуля patch_analyzer устраняет ImportError в patch_checker и обеспечивает компонент анализа структуры патчей.
- patch_analyzer: Рефакторинг patch_analyzer добавляет функцию analyze() и класс PatchAnalyzer, что устраняет ImportError в patch_checker и стабилизирует этап анализа в конвейере патчей.
- patch_checker: Рефакторинг patch_checker использует новые функции patch_analyzer (включая analyze), устраняя ошибки импорта и обеспечивая корректную проверку патчей.
- patch_sanitizer: Рефакторим patch_sanitizer, чтобы гарантировать первичную очистку и нормализацию патчей перед их дальнейшей проверкой и применением в конвейере.
