import os
import time
import base64
import re
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. ЖИВУЧИЙ ВЕБ-СЕРВЕР ДЛЯ RENDER
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Unga Self-Healing is alive!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. КОНФИГУРАЦИЯ И ССЫЛКИ
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
            other_models = [m for m in available if m not in flash_models]
            candidates = flash_models + other_models
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

def ask_gemini(prompt: str) -> str:
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.2}}
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
                r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=25)
                if r.status_code == 200:
                    ans = r.json()['candidates'][0]['content']['parts'][0]['text']
                    return re.sub(r'```[a-zA-Z]*', '', ans).replace('```', '').strip()
                if r.status_code in [429, 503]:
                    rotate_key()
                    time.sleep(2)
            except Exception:
                time.sleep(2)
    return ""

def get_file_content(branch: str, path: str):
    url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/{path}?ref={branch}")
    r = requests.get(url, headers=API_HEADERS, timeout=10)
    if r.status_code == 200:
        return base64.b64decode(r.json().get("content", "")).decode("utf-8")
    return None

def init_branch(branch: str):
    ref_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/ref/heads/main")
    main_sha = requests.get(ref_url, headers=API_HEADERS, timeout=10).json()["object"]["sha"]
    
    del_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{branch}")
    requests.delete(del_url, headers=API_HEADERS, timeout=10)
    time.sleep(1)
    
    create_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs")
    requests.post(create_url, headers=API_HEADERS, json={"ref": f"refs/heads/{branch}", "sha": main_sha}, timeout=10)

def push_code_to_branch(branch: str, path: str, code: str, msg: str):
    file_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/{path}?ref={branch}")
    f_info = requests.get(file_url, headers=API_HEADERS, timeout=10)
    sha = f_info.json().get("sha") if f_info.status_code == 200 else None

    payload = {
        "message": msg,
        "content": base64.b64encode(code.encode("utf-8")).decode("utf-8"),
        "branch": branch
    }
    if sha:
        payload["sha"] = sha
        
    put_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/{path}")
    r = requests.put(put_url, headers=API_HEADERS, json=payload, timeout=10)
    return r.status_code in [200, 201]

def watch_arena_run(branch: str, exclude_run_id=None):
    print(f"[*] Ждем запуска Арены Actions...")
    time.sleep(6)
    runs_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/actions/runs?branch={branch}")
    
    for _ in range(15):
        r = requests.get(runs_url, headers=API_HEADERS, timeout=10)
        if r.status_code == 200:
            runs = r.json().get("workflow_runs", [])
            if runs:
                latest = runs[0]
                run_id = latest.get("id")
                
                # Пропускаем старый запуск, если ждем результат нового коммита
                if exclude_run_id and run_id == exclude_run_id:
                    time.sleep(4)
                    continue

                status = latest.get("status")
                conclusion = latest.get("conclusion")
                print(f"[~] Арена: run #{run_id} | статус: {status} | вердикт: {conclusion}")
                
                if status == "completed":
                    return conclusion == "success", run_id
        time.sleep(5)
    return False, None

def extract_arena_error_log(run_id: int) -> str:
    print(f"[*] Вскрываем логи упавшего запуска #{run_id}...")
    jobs_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/actions/runs/{run_id}/jobs")
    r = requests.get(jobs_url, headers=API_HEADERS, timeout=10)
    if r.status_code != 200:
        return "Не удалось получить список jobs."
        
    jobs = r.json().get("jobs", [])
    failed_job = next((j for j in jobs if j.get("conclusion") == "failure"), None)
    if not failed_job:
        return "Упавший job не обнаружен."

    job_id = failed_job.get("id")
    log_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/actions/jobs/{job_id}/logs")
    log_res = requests.get(log_url, headers=API_HEADERS, timeout=15)
    
    if log_res.status_code == 200:
        full_log = log_res.text
        # Вырезаем фрагмент с тестами unittest (от слова Traceback или FAIL до конца)
        match = re.search(r'(FAIL:.*|Traceback.*|ERROR:.*)', full_log, re.DOTALL)
        if match:
            # Ограничиваем лог последними 1200 символами, чтобы не забивать контекст
            return match.group(0)[-1200:].strip()
        return full_log[-800:].strip()
    return "Логи недоступны."

def merge_and_cleanup(branch: str):
    print(f"[*] Мутация выжила! Вливаем в main...")
    merge_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/merges")
    requests.post(merge_url, headers=API_HEADERS, json={"base": "main", "head": branch, "commit_message": "ЭВОЛЮЦИЯ: Код исцелен и слит в main"}, timeout=10)
    
    del_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{branch}")
    requests.delete(del_url, headers=API_HEADERS, timeout=10)
    print(f"[+] Слияние завершено, ветка '{branch}' стерта.")

def run_self_healing_evolution():
    branch = "unga-mutation-v1"
    print("\n[!] === ЗАПУСК ПРОГРАММЫ САМОИСЦЕЛЕНИЯ ===")
    
    init_branch(branch)
    current_code = get_file_content("main", "victim.py")
    last_run_id = None
    
    # 1. Первая попытка: намеренно сырая генерация
    initial_prompt = (
        "Ты — мутатор кода. Вот файл victim.py:\n\n"
        f"{current_code}\n\n"
        "ЗАДАЧА: Сделай так, чтобы solve_task(a, b) складывала числа и строковые числа. "
        "ТРЕБОВАНИЕ: Верни ТОЛЬКО валидный код Python без комментариев и без markdown."
    )
    
    print("[*] Генерация первой мутации...")
    mutated_code = ask_gemini(initial_prompt)
    if not mutated_code:
        print("[-] Мутация не создана.")
        return

    push_code_to_branch(branch, "victim.py", mutated_code, "Попытка #1")
    passed, last_run_id = watch_arena_run(branch)

    # 2. Цикл Рефлексии (до 3 попыток исцеления при сбое)
    attempt = 1
    max_healing_attempts = 3

    while not passed and attempt <= max_healing_attempts:
        print(f"\n[!] ПОПЫТКА ИСЦЕЛЕНИЯ #{attempt} ИЗ {max_healing_attempts}")
        error_log = extract_arena_error_log(last_run_id)
        print(f"[!] СНЯТЫЙ ТРЕЙСБЕК ОШИБКИ:\n{error_log}\n")

        healing_prompt = (
            "Ты — автономная система самоисцеления кода.\n"
            f"Текущий нерабочий код victim.py:\n{mutated_code}\n\n"
            f"Арена GitHub Actions упала со следующей ошибкой:\n{error_log}\n\n"
            "ЗАДАЧА: Исправь код так, чтобы ошибка устранилась и ВСЕ проверки прошли. "
            "Обрати особое внимание: если в solve_task передана невалидная строка (не число) — должен выбрасываться ValueError! "
            "ТРЕБОВАНИЕ: Верни ТОЛЬКО чистый код Python без markdown (без ```python), без текста."
        )

        print("[*] Gemini анализирует ошибку и пишет патч...")
        mutated_code = ask_gemini(healing_prompt)
        
        push_code_to_branch(branch, "victim.py", mutated_code, f"Исцеление: попытка #{attempt}")
        passed, last_run_id = watch_arena_run(branch, exclude_run_id=last_run_id)
        attempt += 1

    # 3. Финал
    if passed:
        print("\n==========================================")
        print("  [+] САМОИСЦЕЛЕНИЕ УСПЕШНО! КОД ВЫЖИЛ!  ")
        print("==========================================")
        merge_and_cleanup(branch)
    else:
        print("\n==========================================")
        print("  [-] ПРИМАТ ПОГИБ ПОСЛЕ ВСЕХ ПОПЫТОК.   ")
        print("==========================================\n")
        # Удаляем провальную ветку
        requests.delete(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{branch}"), headers=API_HEADERS)

if __name__ == "__main__":
    try:
        run_self_healing_evolution()
    except Exception as e:
        print(f"[!] Критический сбой: {e}")
    threading.Event().wait()
