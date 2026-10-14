import logging
import io

logger = logging.getLogger(__name__)

class LessonParserError(Exception):
    """Исключение, возникающее при ошибках парсинга уроков."""
    pass

class LessonParser:
    def __init__(self, git_inspector):
        self.git_inspector = git_inspector

    def _get_history(self, max_commits=None):
        """Вспомогательный метод для получения истории коммитов с гибкой обработкой сигнатуры."""
        if not hasattr(self.git_inspector, 'get_history') and not hasattr(self.git_inspector, 'get_commit_history'):
            return []

        if max_commits is not None:
            try:
                return self.git_inspector.get_history(max_count=max_commits)
            except TypeError:
                try:
                    return self.git_inspector.get_history()
                except Exception:
                    if hasattr(self.git_inspector, 'get_commit_history'):
                        return self.git_inspector.get_commit_history(max_count=max_commits)
                    raise
            except Exception:
                if hasattr(self.git_inspector, 'get_commit_history'):
                    return self.git_inspector.get_commit_history(max_count=max_commits)
                raise
        else:
            if hasattr(self.git_inspector, 'get_history'):
                try:
                    return self.git_inspector.get_history()
                except Exception:
                    if hasattr(self.git_inspector, 'get_commit_history'):
                        return self.git_inspector.get_commit_history()
                    raise
            elif hasattr(self.git_inspector, 'get_commit_history'):
                return self.git_inspector.get_commit_history()
            return []

    def _get_filenames_for_commit(self, c_hash):
        """Получает список имён файлов, изменённых в коммите."""
        filenames = []

        if hasattr(self.git_inspector, 'get_changed_files'):
            try:
                res = self.git_inspector.get_changed_files(c_hash)
                if isinstance(res, list):
                    filenames.extend(res)
                elif isinstance(res, str):
                    filenames.append(res)
            except Exception:
                pass

        if hasattr(self.git_inspector, 'get_latest_changes'):
            try:
                res = self.git_inspector.get_latest_changes()
                if isinstance(res, list):
                    filenames.extend(res)
                elif isinstance(res, str):
                    for line in res.splitlines():
                        if line.startswith("diff --git a/"):
                            parts = line.split()
                            if len(parts) >= 3 and parts[2].startswith("b/"):
                                filenames.append(parts[2][2:])
                        elif line.startswith("+++ b/"):
                            filenames.append(line[6:].strip())
            except Exception:
                pass

        if hasattr(self.git_inspector, 'get_file_diff'):
            try:
                res = self.git_inspector.get_file_diff(c_hash)
                if isinstance(res, str):
                    for line in res.splitlines():
                        if line.startswith("diff --git a/"):
                            parts = line.split()
                            if len(parts) >= 3 and parts[2].startswith("b/"):
                                filenames.append(parts[2][2:])
                        elif line.startswith("+++ b/"):
                            filenames.append(line[6:].strip())
            except Exception:
                pass

        if not filenames:
            filenames = [c_hash, ""]

        seen = set()
        dedup = []
        for f in filenames:
            if isinstance(f, str) and f not in seen:
                seen.add(f)
                dedup.append(f)
        return dedup

    def _read_content_from_obj(self, res):
        """Преобразует возвращённый объект (str, bytes, io.BytesIO) в строку utf-8."""
        if res is None:
            return None
        if isinstance(res, str):
            return res if res else None
        if isinstance(res, bytes):
            if not res:
                return None
            try:
                return res.decode('utf-8')
            except UnicodeDecodeError:
                return res.decode('latin1', errors='ignore')
        if hasattr(res, 'read'):
            try:
                b = res.read()
                if isinstance(b, bytes):
                    if not b:
                        return None
                    try:
                        return b.decode('utf-8')
                    except UnicodeDecodeError:
                        return b.decode('latin1', errors='ignore')
                elif isinstance(b, str):
                    return b if b else None
            except Exception:
                pass
        return None

    def parse_lessons(self):
        """Парсит историю репозитория и извлекает уроки (ошибки и победы)."""
        forbidden_chars = {'§', '©', '®', '™', 'ø'}
        lessons = []
        
        try:
            history = self._get_history()
        except Exception as e:
            logger.error("Ошибка при получении истории коммитов в parse_lessons: %s", e)
            return []

        if not history:
            return []

        for commit in history:
            if not isinstance(commit, dict) or 'hash' not in commit:
                logger.warning("Некорректная структура коммита: %s", commit)
                continue
            
            c_hash = commit.get('hash')
            msg = commit.get('message', '')

            # Читаем файл на момент коммита
            try:
                filenames = self._get_filenames_for_commit(c_hash)
                content_str = None
                read_errors = []

                for fname in filenames:
                    try:
                        file_obj = self.git_inspector.read_file_at_commit(c_hash, fname)
                        parsed = self._read_content_from_obj(file_obj)
                        if parsed is not None:
                            content_str = parsed
                            break
                    except Exception as e:
                        read_errors.append(e)

                if content_str is None:
                    if read_errors:
                        raise read_errors[0]
                    raise ValueError("Файл не найден")

                # Проверка на запрещенные символы
                for char in forbidden_chars:
                    if char in content_str or char in msg:
                        raise LessonParserError(f"Найден запрещенный символ: {char}")
                        
                lessons.append({
                    'commit': c_hash,
                    'description': msg,
                    'content': content_str
                })
            except LessonParserError:
                raise
            except Exception as read_err:
                for char in forbidden_chars:
                    if char in msg:
                        raise LessonParserError(f"Найден запрещенный символ: {char}")

                logger.warning("Не удалось прочитать файл для коммита %s: %s", c_hash, read_err)
                lessons.append({
                    'commit': c_hash,
                    'description': msg,
                    'content': msg
                })
            
        return lessons

    def extract_lessons(self, max_commits=10):
        """Интеграционный метод для извлечения уроков с фильтрацией запрещенных слов."""
        forbidden_words = {"запрещено"}
        lessons = []
        
        try:
            history = self._get_history(max_commits=max_commits)
            if history is None:
                return []
                
            for commit in history:
                if not isinstance(commit, dict):
                    continue
                c_hash = commit.get('hash')
                msg = commit.get('message', '')
                
                content = msg
                try:
                    filenames = self._get_filenames_for_commit(c_hash)
                    for fname in filenames:
                        file_obj = self.git_inspector.read_file_at_commit(c_hash, fname)
                        parsed = self._read_content_from_obj(file_obj)
                        if parsed is not None:
                            content = parsed
                            break
                except Exception as file_err:
                    logger.debug("Не удалось прочитать файл в extract_lessons для коммита %s: %s", c_hash, file_err)

                # Фильтрация запрещенных слов
                skip = False
                for word in forbidden_words:
                    if word in content or word in msg:
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
