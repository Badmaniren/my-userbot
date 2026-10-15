import logging
import io

logger = logging.getLogger(__name__)

class LessonParserError(Exception):
    """Исключение, возникающее при ошибках парсинга уроков."""
    pass

class LessonParser:
    def __init__(self, git_inspector):
        self.git_inspector = git_inspector

    def parse_lessons(self):
        """Парсит историю репозитория и извлекает уроки (ошибки и победы)."""
        forbidden_chars = {'§', '©', '®', '™', 'ø'}
        lessons = []
        
        history = self.git_inspector.get_history()
        changes = self.git_inspector.get_latest_changes()
        
        if not history and not changes:
            return []

        for commit in history:
            if not isinstance(commit, dict) or 'hash' not in commit:
                logger.warning("Некорректная структура коммита: %s", commit)
                continue
            
            c_hash = commit.get('hash')
            msg = commit.get('message', '')
            
            # Читаем файл на момент коммита, если поддерживается
            try:
                file_obj = None
                if hasattr(self.git_inspector, 'get_changed_files_at_commit'):
                    changed_files = self.git_inspector.get_changed_files_at_commit(c_hash)
                    if changed_files:
                        file_obj = self.git_inspector.read_file_at_commit(c_hash, changed_files[0])
                
                if not file_obj:
                    file_obj = self.git_inspector.read_file_at_commit(c_hash, "")

                if file_obj:
                    content_bytes = file_obj.read()
                    
                    # Проверка на запрещенные символы
                    try:
                        content_str = content_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        content_str = content_bytes.decode('latin1', errors='ignore')
                        
                    for char in forbidden_chars:
                        if char in content_str or char in msg:
                            raise LessonParserError(f"Найден запрещенный символ: {char}")
                            
                    lessons.append({
                        'commit': c_hash,
                        'description': msg,
                        'content': content_str
                    })
                else:
                    for char in forbidden_chars:
                        if char in msg:
                            raise LessonParserError(f"Найден запрещенный символ: {char}")

                    lessons.append({
                        'commit': c_hash,
                        'description': msg,
                        'content': msg
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
            
        return lessons

    def extract_lessons(self, max_commits=10):
        """Интеграционный метод для извлечения уроков с фильтрацией запрещенных слов."""
        forbidden_words = {"запрещено"}
        lessons = []
        
        try:
            history = self.git_inspector.get_history(max_count=max_commits)
        except TypeError:
            try:
                history = self.git_inspector.get_history()
            except TypeError:
                history = []
        if history is None:
            return []
            
        for commit in history:
            if not isinstance(commit, dict):
                continue
            c_hash = commit.get('hash')
            msg = commit.get('message', '')
            
            content = msg
            try:
                file_obj = None
                if hasattr(self.git_inspector, 'get_changed_files_at_commit'):
                    changed_files = self.git_inspector.get_changed_files_at_commit(c_hash)
                    if changed_files:
                        file_obj = self.git_inspector.read_file_at_commit(c_hash, changed_files[0])
                
                if not file_obj:
                    file_obj = self.git_inspector.read_file_at_commit(c_hash, "")

                if file_obj:
                    raw_content = file_obj.read()
                    if isinstance(raw_content, bytes):
                        content = raw_content.decode('utf-8', errors='ignore')
                    else:
                        content = str(raw_content)
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
            
        return lessons