import logging
import io
import re

logger = logging.getLogger(__name__)

class LessonParserError(Exception):
    """Исключение, возникающее при ошибках парсинга уроков."""
    pass

class LessonParser:
    def __init__(self, git_inspector=None):
        self.git_inspector = git_inspector

    def parse_lessons(self, max_commits=10):
        """Парсит историю репозитория и извлекает уроки (ошибки и победы)."""
        forbidden_chars = {'§', '©', '®', '™', 'ø'}
        lessons = []
        
        try:
            if not self.git_inspector:
                return []

            history = None
            if hasattr(self.git_inspector, 'get_history'):
                try:
                    history = self.git_inspector.get_history()
                except Exception as hist_err:
                    logger.warning("Не удалось получить историю через get_history: %s", hist_err)
                    raise
            elif hasattr(self.git_inspector, 'get_commit_history'):
                try:
                    history = self.git_inspector.get_commit_history(max_count=max_commits)
                except Exception as hist_err:
                    logger.warning("Не удалось получить историю через get_commit_history: %s", hist_err)
                    raise

            changes = ""
            if hasattr(self.git_inspector, 'get_latest_changes'):
                try:
                    changes = self.git_inspector.get_latest_changes()
                except Exception as ch_err:
                    logger.debug("Не удалось получить последние изменения: %s", ch_err)

            if not history and not changes:
                return []

            if history is None:
                history = []

            for commit in history:
                if not isinstance(commit, dict) or 'hash' not in commit:
                    logger.warning("Некорректная структура коммита: %s", commit)
                    continue
                
                c_hash = commit.get('hash')
                msg = commit.get('message', '')
                
                # Читаем файл или содержимое коммита
                try:
                    content_str = None
                    if hasattr(self.git_inspector, 'read_file_at_commit'):
                        file_obj = self.git_inspector.read_file_at_commit(c_hash, "")
                        if file_obj is not None:
                            if hasattr(file_obj, 'read'):
                                content_bytes = file_obj.read()
                                if isinstance(content_bytes, str):
                                    content_str = content_bytes
                                elif isinstance(content_bytes, bytes):
                                    try:
                                        content_str = content_bytes.decode('utf-8')
                                    except UnicodeDecodeError:
                                        content_str = content_bytes.decode('latin1', errors='ignore')
                            elif isinstance(file_obj, str):
                                content_str = file_obj
                            elif isinstance(file_obj, bytes):
                                try:
                                    content_str = file_obj.decode('utf-8')
                                except UnicodeDecodeError:
                                    content_str = file_obj.decode('latin1', errors='ignore')

                    if (not content_str or content_str.startswith("tree ")) and hasattr(self.git_inspector, 'get_file_diff'):
                        diff_text = self.git_inspector.get_file_diff(c_hash)
                        if diff_text:
                            content_str = diff_text

                    if content_str is None:
                        content_str = msg

                    for char in forbidden_chars:
                        if char in content_str:
                            raise LessonParserError(f"Найден запрещенный символ: {char}")
                            
                    lessons.append({
                        'commit': c_hash,
                        'description': msg,
                        'content': content_str
                    })

                except LessonParserError:
                    raise
                except Exception as read_err:
                    logger.warning("Не удалось прочитать файл для коммита %s: %s", c_hash, read_err)
                    lessons.append({
                        'commit': c_hash,
                        'description': msg,
                        'content': msg
                    })

        except LessonParserError:
            raise
        except Exception as e:
            raise LessonParserError(str(e))
            
        return lessons

    def parse(self, max_commits=10):
        """Псевдоним для parse_lessons."""
        return self.parse_lessons(max_commits=max_commits)

    def extract_lessons(self, max_commits=10):
        """Интеграционный метод для извлечения уроков с фильтрацией запрещенных слов."""
        forbidden_words = {"запрещено"}
        lessons = []
        
        try:
            if not self.git_inspector:
                return []

            history = None
            if hasattr(self.git_inspector, 'get_history'):
                history = self.git_inspector.get_history(max_count=max_commits)
            elif hasattr(self.git_inspector, 'get_commit_history'):
                history = self.git_inspector.get_commit_history(max_count=max_commits)

            if history is None:
                return []
                
            for commit in history:
                if not isinstance(commit, dict):
                    continue
                c_hash = commit.get('hash')
                msg = commit.get('message', '')
                
                content = msg
                try:
                    if hasattr(self.git_inspector, 'read_file_at_commit'):
                        file_obj = self.git_inspector.read_file_at_commit(c_hash, "")
                        if file_obj is not None:
                            if hasattr(file_obj, 'read'):
                                raw = file_obj.read()
                                if isinstance(raw, str):
                                    content = raw
                                elif isinstance(raw, bytes):
                                    content = raw.decode('utf-8', errors='ignore')
                            elif isinstance(file_obj, str):
                                content = file_obj
                            elif isinstance(file_obj, bytes):
                                content = file_obj.decode('utf-8', errors='ignore')
                    if (not content or content.startswith("tree ")) and hasattr(self.git_inspector, 'get_file_diff'):
                        diff_text = self.git_inspector.get_file_diff(c_hash)
                        if diff_text:
                            content = diff_text
                except Exception as file_err:
                    logger.debug("Не удалось прочитать файл в extract_lessons для коммита %s: %s", c_hash, file_err)

                # Фильтрация запрещенных слов
                skip = False
                for word in forbidden_words:
                    if word in content:
                        skip = True
                        break
                
                if skip:
                    continue

                lessons.append({
                    "commit": c_hash,
                    "content": content
                })
        except Exception as inspector_err:
            logger.error("Ошибка при работе инспектора в extract_lessons: %s", inspector_err)
            return []
            
        return lessons

    def get_context_for_file(self, file_path, max_commits=10):
        """Получает контекст истории для указанного файла."""
        lessons = self.parse_lessons(max_commits=max_commits)
        return [l for l in lessons if file_path in l.get('content', '') or file_path in l.get('description', '')]

    def analyze_file_history(self, file_path, max_commits=10):
        """Анализирует историю изменений файла."""
        return self.get_context_for_file(file_path, max_commits=max_commits)

    def parse_latest_change(self):
        """Парсит последнее изменение."""
        lessons = self.parse_lessons(max_commits=1)
        return lessons[0] if lessons else None

    def parse_lesson_history(self, max_commits=10):
        """Парсит историю уроков."""
        return self.parse_lessons(max_commits=max_commits)

    def extract_failure_history(self, max_commits=10):
        """Извлекает историю неудач/ошибок из коммитов."""
        lessons = self.parse_lessons(max_commits=max_commits)
        failures = []
        for l in lessons:
            content = l.get('content', '') + ' ' + l.get('description', '')
            if any(term in content.lower() for term in ['error', 'fail', 'bug', 'fix', 'сбой', 'ошибка', 'anticheat']):
                failures.append(l)
        return failures

    def get_fix_commits(self, max_commits=10):
        """Извлекает коммиты-исправления."""
        lessons = self.parse_lessons(max_commits=max_commits)
        return [l for l in lessons if 'fix' in l.get('description', '').lower() or 'исправлен' in l.get('description', '').lower()]

    def parse_anticheat_errors(self, content_or_commit_hash=None):
        """Извлекает ошибки античита по шаблону ANTICHEAT_VIOLATION_\\w+."""
        text = str(content_or_commit_hash or '')
        if self.git_inspector and content_or_commit_hash and hasattr(self.git_inspector, 'get_file_diff'):
            try:
                diff = self.git_inspector.get_file_diff(content_or_commit_hash)
                if diff:
                    text += '\n' + str(diff)
            except Exception as diff_err:
                logger.debug("Ошибка при получении diff в parse_anticheat_errors: %s", diff_err)
        return re.findall(r'ANTICHEAT_VIOLATION_\w+', text)

    def extract_error_patterns(self, content):
        """Извлекает шаблоны ошибок из текста."""
        text = str(content or '')
        anticheat_errors = self.parse_anticheat_errors(text)
        general_errors = re.findall(r'(?:Error|Exception|Traceback|Failed|Сбой|Ошибка):[^\n]+', text)
        return list(set(anticheat_errors + general_errors))

    def prepare_hypothesis_data(self, max_commits=10):
        """Подготавливает данные для генератора гипотез."""
        lessons = self.parse_lessons(max_commits=max_commits)
        failures = self.extract_failure_history(max_commits=max_commits)
        error_patterns = []
        for f in failures:
            error_patterns.extend(self.extract_error_patterns(f.get('content', '')))
        return {
            'lessons': lessons,
            'failures': failures,
            'error_patterns': list(set(error_patterns))
        }
