import os
import time
import base64
import re
import json
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. ЖИВУЧИЙ ВЕБ-СЕРВЕР ДЛЯ RENDER
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Pithecanthropus Triad is awake!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. ИНФРАСТРУКТУРА И СЕТЬ
def clean_url(url: str) -> str:
    return re.sub(r'\[.*?\]\(\vert{}\)', '', url).strip()

API_HOST = "generativelanguage.googleapis.com"
API_BASE = "https://" + API_HOST + "/v1beta/"

GITHUB_HOST = "api.github.com"
GITHUB_BASE = "https://" + GITHUB_HOST + "/repos/"

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.environ.get("GITHUB_REPO", "").strip()
RAW_KEYS = os.environ.get("GEMINI_API_KEY", "").strip()
API_KEYS = [k.strip() for k in RAW_KEYS.split(",") if k.strip()]
KEY_INDEX = 0

API_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_current_key():
    global KEY_INDEX
    return API_KEYS[KEY_INDEX % len(API_KEYS)] if API_KEYS else ""

def rotate_key():
    global KEY_INDEX
    if len(API_KEYS) > 1:
        KEY_INDEX = (KEY_INDEX + 1) % len(API_KEYS)
        print(f"[!] Смена ключа Gemini на индекс #{KEY_INDEX}")

def get_viable_models(key: str) -> list:
    url = clean_url(f"{API_BASE}models?key={key}")
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            models = r.json().get("models", [])
            available = [m["name"] for m in models if "generateContent" in m.get("supportedGenerationMethods", [])]
            flash_models = [m for m in available if "flash" in m.lower() and "preview" not in m.lower()]
            candidates = flash_models + [m for m in available if m not in flash_models]
            viable = []
            for m in candidates:
                test_url = clean_url(f"{API_BASE}{m}:generateContent?key={key}")
                try:
                    res = requests.post(test_url, json={"contents": [{"parts": [{"text": "hi"}]}]}, timeout=8)
                    if res.status_code == 200:
                        viable.append(m)
                        if len(viable) >= 2:
                            break
                except Exception:
                    continue
            return viable
    except Exception:
        pass
    return []

def ask_gemini(prompt: str, json_mode: bool = False) -> str:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "responseMimeType": "application/json" if json_mode else "text/plain"
        }
    }
    for _ in range(4):
        key = get_current_key()
        models = get_viable_models(key)
        if not models:
            rotate_key()
            time.sleep(2)
            continue
        for model in models:
            url = clean_url(f"{API_BASE}{model}:generateContent?key={key}")
            try:
                r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
                if r.status_code == 200:
                    ans = r.json()['candidates'][0]['content']['parts'][0]['text']
                    if not json_mode:
                        return re.sub(r'```[a-zA-Z]*', '', ans).replace('```', '').strip()
                    return ans.strip()
                if r.status_code in [429, 503]:
                    rotate_key()
                    time.sleep(2)
            except Exception:
                time.sleep(2)
    return ""

# 3. НАВИГАЦИЯ ПО РЕПОЗИТОРИЮ
def get_existing_skills() -> list:
    url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/skills?ref=main")
    r = requests.get(url, headers=API_HEADERS, timeout=10)
    if r.status_code == 200:
        return [f["name"] for f in r.json() if f["name"].endswith(".py") and f["name"] != "__init__.py"]
    return []

def get_main_sha() -> str:
    url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/ref/heads/main")
    r = requests.get(url, headers=API_HEADERS, timeout=10)
    return r.json()["object"]["sha"] if r.status_code == 200 else ""

def prepare_branch(branch: str, base_sha: str):
    del_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{branch}")
    requests.delete(del_url, headers=API_HEADERS, timeout=10)
    time.sleep(1)
    create_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs")
    requests.post(create_url, headers=API_HEADERS, json={"ref": f"refs/heads/{branch}", "sha": base_sha}, timeout=10)

def commit_file_to_branch(branch: str, path: str, content: str, msg: str):
    file_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/{path}?ref={branch}")
    f_info = requests.get(file_url, headers=API_HEADERS, timeout=10)
    sha = f_info.json().get("sha") if f_info.status_code == 200 else None

    payload = {
        "message": msg,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": branch
    }
    if sha:
        payload["sha"] = sha
    requests.put(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/{path}"), headers=API_HEADERS, json=payload, timeout=10)

def watch_arena(branch: str, exclude_id=None):
    time.sleep(8)
    runs_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/actions/runs?branch={branch}")
    for _ in range(16):
        r = requests.get(runs_url, headers=API_HEADERS, timeout=10)
        if r.status_code == 200:
            runs = r.json().get("workflow_runs", [])
            if runs:
                latest = runs[0]
                run_id = latest.get("id")
                if exclude_id and run_id == exclude_id:
                    time.sleep(4)
                    continue
                if latest.get("status") == "completed":
                    return latest.get("conclusion") == "success", run_id
        time.sleep(5)
    return False, None

def extract_traceback(run_id: int) -> str:
    jobs_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/actions/runs/{run_id}/jobs")
    r = requests.get(jobs_url, headers=API_HEADERS, timeout=10)
    if r.status_code != 200:
        return ""
    jobs = r.json().get("jobs", [])
    failed = next((j for j in jobs if j.get("conclusion") == "failure"), None)
    if not failed:
        return ""
    log_res = requests.get(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/actions/jobs/{failed['id']}/logs"), headers=API_HEADERS, timeout=15)
    if log_res.status_code == 200:
        match = re.search(r'(FAIL:.*|Traceback.*|ERROR:.*)', log_res.text, re.DOTALL)
        return match.group(0)[-1200:].strip() if match else log_res.text[-800:].strip()
    return ""

# 4. ТРИАДА СОЗНАНИЯ
def dream_new_skill(existing_skills: list) -> dict:
    prompt = (
        "Ты — Фантазер в триаде автономного выживания. Твоя директива: ТЕХНО-ПАРАЗИТИЗМ. "
        "Ты заперт на бесплатном сервере Render (512MB RAM, без денег) с доступом в GitHub и Gemini API. "
        f"Список уже готовых навыков в папке skills: {existing_skills}\n\n"
        "ЗАДАЧА: Придумай ОДИН новый автономный утилитарный инструмент (модуль Python) для папки skills/. "
        "Он должен расширять выживаемость или возможности агента: парсинг бесплатных открытых данных (RSS, HTTP заголовки, crypto ticker), "
        "безопасная сериализация, чистка текста от мусора, кэширование в файлы.\n"
        "ТРЕБОВАНИЕ: Модуль должен использовать ТОЛЬКО стандартную библиотеку Python или requests. Никаких платных ключей!\n"
        "Ответь строго JSON-объектом со следующими ключами:\n"
        "{\n"
        '  "module_name": "имя_модуля_без_py (например rss_lite или proxy_check)",\n'
        '  "description": "что делает модуль в 1 предложении",\n'
        '  "class_or_func": "основной класс или функции, которые должны быть реализованы"\n'
        "}"
    )
    raw = ask_gemini(prompt, json_mode=True)
    try:
        return json.loads(raw)
    except Exception:
        # Резервный навык на случай сбоя парсинга JSON
        return {
            "module_name": "text_sanitizer",
            "description": "Очистка текста от HTML, Markdown и опасных управляющих символов",
            "class_or_func": "sanitize_text(text: str) -> str, extract_links(text: str) -> list"
        }

def architect_write_tests(skill_info: dict) -> str:
    prompt = (
        "Ты — Архитектор-Инквизитор. Твоя задача — написать жесткий файл юнит-тестов для модуля, "
        f"который задумал Фантазер.\nИнфо о модуле:\n{json.dumps(skill_info, ensure_ascii=False)}\n\n"
        f"Модуль будет лежать по пути: skills.{skill_info['module_name']}\n\n"
        "ТРЕБОВАНИЯ К ТЕСТАМ:\n"
        "1. Использовать модуль `unittest`.\n"
        f"2. Импортировать тестируемый функционал через: `from skills.{skill_info['module_name']} import ...`\n"
        "3. Написать 4-6 строгих тестов, включая краевые случаи (пустые строки, некорректные типы).\n"
        "4. Тесты должны выполняться БЕЗ реальных внешних сетевых запросов (если модуль сетевой — использовать mock или тестировать логику парсинга входных данных/строк).\n"
        "5. Верни ТОЛЬКО валидный код Python файла тестов без markdown (без ```python)."
    )
    return ask_gemini(prompt)

def unga_write_implementation(skill_info: dict, test_code: str, error_log: str = "") -> str:
    context = f"Лог падения тестов на Арене:\n{error_log}\n" if error_log else "Первая попытка реализации."
    prompt = (
        "Ты — Унга, работяга-кодер. Тебе нужно написать модуль, удовлетворяющий жестким тестам Архитектора.\n"
        f"Название модуля: skills/{skill_info['module_name']}.py\n"
        f"Описание задачи: {skill_info['description']}\n\n"
        f"КОД ТЕСТОВ (ОБЯЗАН ИХ ПРОЙТИ):\n{test_code}\n\n"
        f"{context}\n\n"
        "ТРЕБОВАНИЯ:\n"
        "1. Напиши полную, рабочую реализацию модуля.\n"
        "2. Используй только стандартную библиотеку Python или requests.\n"
        "3. Верни ТОЛЬКО чистый код Python файла без markdown (без ```python) и без комментариев."
    )
    return ask_gemini(prompt)

# 5. ГЛАВНЫЙ ЭВОЛЮЦИОННЫЙ ЦИКЛ
def run_triad_cycle():
    print("\n==========================================")
    print("   ПИТЕКАНТРОП: ЗАПУСК ЭВОЛЮЦИИ ТРИАДЫ    ")
    print("==========================================")
    
    existing = get_existing_skills()
    print(f"[*] Освоенные навыки в skills/: {existing if existing else 'пока пусто'}")

    print("\n[1/4] ФАНТАЗЕР: Поиск новой точки экспансии...")
    idea = dream_new_skill(existing)
    mod_name = re.sub(r'[^a-zA-Z0-9_]', '', idea.get("module_name", "tool").lower())
    print(f"[+] Задумана новая мутация: '{mod_name}'")
    print(f"[*] Назначение: {idea.get('description')}")

    print("\n[2/4] АРХИТЕКТОР: Создание контракта и тестов...")
    test_code = architect_write_tests(idea)
    
    branch = f"unga-skill-{mod_name}"
    main_sha = get_main_sha()
    prepare_branch(branch, main_sha)
    
    test_path = f"test_{mod_name}.py"
    skill_path = f"skills/{mod_name}.py"
    
    # Создаем __init__.py в skills если папка пустая
    commit_file_to_branch(branch, "skills/__init__.py", "# unga skills package\n", "Init skills package")
    commit_file_to_branch(branch, test_path, test_code, f"Архитектор: тесты для {mod_name}")

    print("\n[3/4] УНГА: Первичная сборка модуля...")
    impl_code = unga_write_implementation(idea, test_code)
    commit_file_to_branch(branch, skill_path, impl_code, f"Унга: реализация {mod_name}")

    print(f"[*] Отправлено на Арену Actions. Ждем...")
    passed, run_id = watch_arena(branch)
    
    # 4. Цикл Рефлексии при падении
    attempts = 1
    while not passed and attempts <= 3:
        print(f"\n[!] САМОИСЦЕЛЕНИЕ: Попытка #{attempts} для модуля '{mod_name}'")
        err = extract_traceback(run_id)
        print(f"[!] Ошибка тестов:\n{err}\n")
        
        impl_code = unga_write_implementation(idea, test_code, error_log=err)
        commit_file_to_branch(branch, skill_path, impl_code, f"Унга исцеление #{attempts}")
        passed, run_id = watch_arena(branch, exclude_id=run_id)
        attempts += 1

    if passed:
        print(f"\n[+] МОДУЛЬ '{mod_name}' ВЫЖИЛ И ДОКАЗАЛ ПОЛЬЗУ!")
        requests.post(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/merges"), headers=API_HEADERS, json={
            "base": "main", "head": branch, "commit_message": f"ЭВОЛЮЦИЯ: Освоен навык skills/{mod_name}.py"
        }, timeout=10)
        requests.delete(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{branch}"), headers=API_HEADERS)
        print(f"[+] Навык ассимилирован в main! Ветка удалена.")
    else:
        print(f"\n[-] Мутация '{mod_name}' признана нежизнеспособной и уничтожена.")
        requests.delete(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{branch}"), headers=API_HEADERS)

if __name__ == "__main__":
    try:
        run_triad_cycle()
    except Exception as e:
        print(f"[!!!] Сбой цикла Триады: {e}")
    threading.Event().wait()
