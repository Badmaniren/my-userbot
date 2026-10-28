# Текущий эпик Унги

## Безопасный пайплайн исправления патчей: Санитизация → Проверка → Применение

- patch_sanitizer: Создаем первый модуль нового эпика для первичной очистки и нормализации патчей.
- patch_checker: Рефакторинг модуля patch_checker для успешного прохождения тестов и продвижения по эпику санитизации и проверки патчей.
- patch_analyzer: Stabilizing the analyzer is the critical bridge between sanitization and verification; without a robust analyzer, the pipeline cannot reliably pass the patch to the validator.
- patch_evaluator: Исправление и стабилизация patch_evaluator для завершения шага оценки в безопасном пайплайне патчей.
- patch_verifier: Рефакторинг patch_verifier для прохождения всех провальных тестов и замыкания этапа проверки в конвейере.
