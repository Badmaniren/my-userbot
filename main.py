import os
import sys
import time
import base64
import re
import json
import ast
import io
import zipfile
import html
import requests
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. FAIL-FAST ПРОВЕРКА ОКРУЖЕНИЯ
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.environ.get("GITHUB_REPO", "").strip()
RAW_KEYS = os.environ.get("GEMINI_API_KEY", "").strip()
API_KEYS = [k.strip() for k in RAW_KEYS.split(",") if k.strip()]

TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TG_ADMIN_ID = os.environ.get("TELEGRAM_ADMIN_ID", "").strip()

if not GITHUB_TOKEN or not GITHUB_REPO or not API_KEYS:
    print("[FATAL] Отсутствуют критические переменные окружения (GITHUB_TOKEN, GITHUB_REPO, GEMINI_API_KEY)!")
    sys.exit(1)

MANUAL_TASK_QUEUE = []
HANDLED_JULES_COMMENTS = set()

# 2. СЕРВЕР ЖИЗНИ ДЛЯ RENDER
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Pithecanthropus Hardened Daemon is operational.")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 3. БЕЗОПАСНЫЙ TELEGRAM ДЕМОН (HTML)
def send_tg(text: str, buttons: list = None, keyboard: bool = False):
    if not TG_TOKEN or not TG_ADMIN_ID:
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_ADMIN_ID,
        "text": text[:4000],
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if keyboard:
        payload["reply_markup"] = json.dumps({
            "keyboard": [["📊 /status", "🔁 /jules"], ["⚙️ /build ", "❓ /help"]],
            "resize_keyboard": True,
            "is_persistent": True
        })
    elif buttons:
        payload["reply_markup"] = json.dumps({"inline_keyboard": buttons})
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[!] Ошибка отправки в TG: {e}")

def tg_issue_button(issue_url: str) -> list:
    return [[{"text": "🔗 Открыть задачу для Jules", "url": issue_url}]] if issue_url else None

def answer_tg_callback(callback_query_id: str, text: str = ""):
    if not TG_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/answerCallbackQuery"
    try:
        requests.post(url, json={"callback_query_id": callback_query_id, "text": text[:200]}, timeout=10)
    except Exception:
        pass

def set_tg_commands():
    if not TG_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/setMyCommands"
    commands = [
        {"command": "status", "description": "📊 Текущий статус и эпик"},
        {"command": "build", "description": "⚙️ Поставить задачу вручную"},
        {"command": "jules", "description": "🔁 Реактивировать зависшие Jules-задачи"},
        {"command": "prs", "description": "🔀 Подтянуть main во все отстающие PR"},
        {"command": "cleanup", "description": "🧹 Найти и удалить дубли навыков"},
        {"command": "help", "description": "❓ Список команд"},
    ]
    try:
        requests.post(url, json={"commands": commands}, timeout=10)
    except Exception:
        pass

HELP_TEXT = (
    "🐒 <b>Пульт управления Питекантропом</b>\n"
    "━━━━━━━━━━━━━━━━━━━\n"
    "📊 <code>/status</code> — что бот делает сейчас и какой эпик в работе\n"
    "⚙️ <code>/build &lt;описание&gt;</code> — поставить задачу вручную в очередь\n"
    "🔁 <code>/jules</code> — растолкать зависшие Jules-задачи\n"
    "🔀 <code>/prs</code> — подтянуть main во все отстающие PR\n"
    "🧹 <code>/cleanup</code> — найти дубли навыков и предложить удаление\n"
    "❓ <code>/help</code> — это сообщение\n"
    "━━━━━━━━━━━━━━━━━━━\n"
    "<i>Кнопки внизу экрана дублируют команды — жми, а не печатай.</i>"
)

def run_telegram_listener():
    if not TG_TOKEN or not TG_ADMIN_ID:
        print("[!] Telegram переменные не заданы. Демон связи отключен.")
        return

    offset = 0
    print("[+] Telegram-пульт управления запущен.")
    set_tg_commands()
    send_tg(
        "🐒 <b>Питекантроп на связи!</b>\nДемон запущен, меню команд — снизу экрана.",
        keyboard=True
    )

    while True:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates"
        try:
            r = requests.get(url, params={"offset": offset, "timeout": 20}, timeout=25)
            if r.status_code == 200:
                data = r.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1

                    callback = update.get("callback_query")
                    if callback:
                        cb_chat_id = str(callback.get("message", {}).get("chat", {}).get("id", ""))
                        cb_data = callback.get("data", "")
                        if cb_chat_id != TG_ADMIN_ID:
                            answer_tg_callback(callback["id"])
                            continue
                        if cb_data == "rejules":
                            answer_tg_callback(callback["id"], "Толкаю зависшие задачи...")
                            count = reactivate_stuck_jules_issues()
                            if count:
                                send_tg(f"🔁 Реактивировано Jules-задач: <b>{count}</b>.\nДай ему пару минут забрать их в работу.")
                            else:
                                send_tg("ℹ️ Открытых Jules-задач не найдено — реактивировать нечего.")
                        elif cb_data == "refreshprs":
                            answer_tg_callback(callback["id"], "Обновляю PR от main...")
                            refreshed, dirty_urls = refresh_stuck_prs()
                            msg = f"🔀 Обновлено PR: <b>{refreshed}</b>."
                            if dirty_urls:
                                msg += f"\n⚠️ С настоящими конфликтами: <b>{len(dirty_urls)}</b> (нужна ручная правка)."
                            send_tg(msg)
                        elif cb_data == "confirm_cleanup":
                            answer_tg_callback(callback["id"], "Удаляю дубли...")
                            if PENDING_CLEANUP_PLAN:
                                count = execute_cleanup_plan(PENDING_CLEANUP_PLAN)
                                send_tg(f"🗑 Удалено файлов: <b>{count}</b>.")
                                PENDING_CLEANUP_PLAN.clear()
                            else:
                                send_tg("ℹ️ План очистки устарел или пуст — вызови /cleanup заново.")
                        continue

                    msg = update.get("message", {})
                    chat_id = str(msg.get("chat", {}).get("id", ""))
                    text = msg.get("text", "").strip()
                    text = re.sub(r'^[📊🔁⚙️❓]\s*', '', text)

                    if chat_id != TG_ADMIN_ID:
                        continue

                    if text.startswith("/start"):
                        send_tg(HELP_TEXT, keyboard=True)
                    elif text.startswith("/help"):
                        send_tg(HELP_TEXT)
                    elif text.startswith("/build"):
                        task_desc = text[6:].strip()
                        if task_desc:
                            MANUAL_TASK_QUEUE.append(task_desc)
                            send_tg(f"🫡 <b>Задача принята в очередь</b>\n━━━━━━━━━━━━━━━━━━━\n<code>{html.escape(task_desc)}</code>")
                        else:
                            send_tg("⚠️ Укажи описание задачи после команды:\n<code>/build утилита_для_парсинга</code>")
                    elif text.startswith("/status"):
                        q_len = len(MANUAL_TASK_QUEUE)
                        epic_preview = get_epic_context()
                        if len(epic_preview) > 800:
                            epic_preview = epic_preview[:800] + "..."
                        send_tg(
                            f"📊 <b>Статус</b>\n━━━━━━━━━━━━━━━━━━━\n"
                            f"Работает штатно · задач в очереди: <b>{q_len}</b>\n\n"
                            f"🧭 <b>Текущий эпик</b>\n<pre>{html.escape(epic_preview)}</pre>",
                            buttons=[
                                [{"text": "🔁 Реактивировать зависшие Jules-задачи", "callback_data": "rejules"}],
                                [{"text": "🔀 Обновить отстающие PR от main", "callback_data": "refreshprs"}]
                            ]
                        )
                    elif text.startswith("/jules"):
                        count = reactivate_stuck_jules_issues()
                        if count:
                            send_tg(f"🔁 Реактивировано Jules-задач: <b>{count}</b>.")
                        else:
                            send_tg("ℹ️ Открытых Jules-задач не найдено.")
                    elif text.startswith("/prs"):
                        refreshed, dirty_urls = refresh_stuck_prs()
                        msg = f"🔀 Обновлено PR: <b>{refreshed}</b>."
                        if dirty_urls:
                            msg += f"\n⚠️ С настоящими конфликтами: <b>{len(dirty_urls)}</b> (нужна ручная правка)."
                        send_tg(msg)
                    elif text.startswith("/cleanup"):
                        report, plan = build_cleanup_plan()
                        PENDING_CLEANUP_PLAN.clear()
                        PENDING_CLEANUP_PLAN.extend(plan)
                        buttons = [[{"text": "⚠️ Подтвердить удаление", "callback_data": "confirm_cleanup"}]] if plan else None
                        send_tg(report, buttons=buttons)
                    elif text:
                        send_tg("🤷 Не знаю такой команды.\n" + HELP_TEXT)
        except Exception:
            time.sleep(5)
        time.sleep(1)

threading.Thread(target=run_telegram_listener, daemon=True).start()

# 4. СЕТЬ И КЛИЕНТ GEMINI
def clean_url(url: str) -> str:
    return re.sub(r'\[.*?\]\(\vert{}\)', '', url).strip()

API_HOST = "generativelanguage.googleapis.com"
API_BASE = "https://" + API_HOST + "/v1beta/"
GITHUB_HOST = "api.github.com"
GITHUB_BASE = "https://" + GITHUB_HOST + "/repos/"

KEY_INDEX = 0
MODELS_CACHE = {"models": [], "expires_at": 0, "key": ""}

API_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_current_key():
    global KEY_INDEX
    return API_KEYS[KEY_INDEX % len(API_KEYS)]

def rotate_key():
    global KEY_INDEX, MODELS_CACHE
    if len(API_KEYS) > 1:
        KEY_INDEX = (KEY_INDEX + 1) % len(API_KEYS)
        MODELS_CACHE["expires_at"] = 0
        print(f"[!] Ротация ключа Gemini -> #{KEY_INDEX}")

def get_viable_models(key: str) -> list:
    global MODELS_CACHE
    now = time.time()
    if MODELS_CACHE["key"] == key and MODELS_CACHE["expires_at"] > now and MODELS_CACHE["models"]:
        return MODELS_CACHE["models"]

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
            if viable:
                MODELS_CACHE = {"models": viable, "expires_at": now + 3600, "key": key}
                return viable
    except Exception:
        pass
    return []

def strip_markdown(text: str) -> str:
    cleaned = re.sub(r'^```[a-zA-Z]*\n', '', text.strip(), flags=re.MULTILINE)
    return re.sub(r'```$', '', cleaned.strip(), flags=re.MULTILINE).strip()

def ask_gemini(prompt: str, json_mode: bool = False) -> str:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
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
                    return strip_markdown(ans)
                if r.status_code in [429, 503]:
                    rotate_key()
                    time.sleep(2)
            except Exception:
                time.sleep(2)
    return ""

# 5. GITHUB ОПЕРАЦИИ И ЭСКАЛАЦИЯ ДЛЯ JULES
def get_main_sha() -> str:
    url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/ref/heads/main")
    r = requests.get(url, headers=API_HEADERS, timeout=10)
    return r.json()["object"]["sha"] if r.status_code == 200 else ""

def get_file_content(branch: str, path: str):
    url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/{path}?ref={branch}")
    r = requests.get(url, headers=API_HEADERS, timeout=10)
    if r.status_code == 200:
        return base64.b64decode(r.json().get("content", "")).decode("utf-8")
    return None

def prepare_branch(branch: str, base_sha: str) -> bool:
    ref_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{branch}")
    patch_res = requests.patch(ref_url, headers=API_HEADERS, json={"sha": base_sha, "force": True}, timeout=10)
    if patch_res.status_code == 200:
        return True

    create_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs")
    res = requests.post(create_url, headers=API_HEADERS, json={"ref": f"refs/heads/{branch}", "sha": base_sha}, timeout=10)
    return res.status_code in [200, 201]

def commit_file_to_branch(branch: str, path: str, content: str, msg: str) -> str:
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

    put_res = requests.put(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/{path}"), headers=API_HEADERS, json=payload, timeout=10)
    if put_res.status_code in [200, 201]:
        return put_res.json().get("commit", {}).get("sha", "")
    return ""

def watch_arena_by_sha(expected_sha: str):
    if not expected_sha:
        return False, None
    time.sleep(10)
    runs_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/actions/runs")
    last_seen_id = None

    for _ in range(30):
        r = requests.get(runs_url, headers=API_HEADERS, timeout=10)
        if r.status_code == 200:
            runs = r.json().get("workflow_runs", [])
            target_run = next((run for run in runs if run.get("head_sha") == expected_sha), None)

            if target_run:
                last_seen_id = target_run.get("id")
                if target_run.get("status") == "completed":
                    return target_run.get("conclusion") == "success", last_seen_id
        time.sleep(10)
    return False, last_seen_id

def extract_clean_test_traceback(run_id: int) -> str:
    if not run_id:
        return "Не удалось определить run_id шага тестирования."

    logs_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/actions/runs/{run_id}/logs")
    try:
        r = requests.get(logs_url, headers=API_HEADERS, timeout=30)
        if r.status_code != 200:
            return f"Не удалось скачать архив логов рана (HTTP {r.status_code})."

        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            target_name = next(
                (name for name in z.namelist() if "run tests" in name.lower() or "unittest" in name.lower()),
                None
            )
            if not target_name:
                txt_files = [n for n in z.namelist() if n.endswith(".txt")]
                if not txt_files:
                    return "Архив логов пуст."
                target_name = max(txt_files, key=lambda n: z.getinfo(n).file_size)

            log_text = z.read(target_name).decode("utf-8", errors="ignore")

        lines = log_text.splitlines()
        error_buffer = []
        capture = False

        for line in lines:
            cleaned = re.sub(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s*', '', line).strip()
            if any(marker in cleaned for marker in ["FAIL:", "ERROR:", "Traceback (most recent call last):", "SyntaxError:", "ImportError:", "ModuleNotFoundError:"]):
                capture = True
            if capture:
                if not cleaned.startswith("[command]") and "node-20" not in cleaned.lower():
                    error_buffer.append(cleaned)
                if len(error_buffer) >= 45:
                    break
                if cleaned.startswith("FAILED ("):
                    break

        return "\n".join(error_buffer) if error_buffer else "Лог получен, но блок ошибки не идентифицирован."

    except Exception as e:
        return f"Сбой при извлечении трейсбека: {e}"

def fix_jules_issue_labels() -> int:
    ensure_jules_label_exists()
    url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/issues?state=open&per_page=100")
    fixed = 0
    try:
        r = requests.get(url, headers=API_HEADERS, timeout=10)
        if r.status_code == 200:
            for issue in r.json():
                if "pull_request" in issue:
                    continue
                if not issue.get("title", "").startswith("Jules Task:"):
                    continue
                labels = [l["name"] for l in issue.get("labels", [])]
                if "jules" in labels:
                    continue
                num = issue["number"]
                res = requests.post(
                    clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/issues/{num}/labels"),
                    headers=API_HEADERS, json={"labels": ["jules"]}, timeout=10
                )
                if res.status_code in (200, 201):
                    fixed += 1
    except Exception as e:
        print(f"[!] Ошибка починки меток: {e}")
    return fixed

def ensure_jules_label_exists() -> None:
    url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/labels")
    try:
        res = requests.post(url, headers=API_HEADERS, json={
            "name": "jules",
            "color": "6f42c1",
            "description": "Автоматически подхватывается Jules для исправления"
        }, timeout=10)
        if res.status_code not in [200, 201, 422]:
            print(f"[!] Не удалось создать лейбл jules (HTTP {res.status_code})")
    except Exception as e:
        print(f"[!] Ошибка запроса создания лейбла jules: {e}")

def escalate_to_github_issue(mod_name: str, task_desc: str, last_error: str, branch: str) -> str:
    ensure_jules_label_exists()
    issue_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/issues")
    body = (
        f"### Автоматическая эскалация сбоя от Питекантропа\n\n"
        f"- **Модуль:** `skills/{mod_name}.py`\n"
        f"- **Рабочая ветка:** `{branch}`\n"
        f"- **Исходная цель:** {task_desc}\n\n"
        f"#### Трейсбек последней ошибки из GitHub Actions:\n```text\n{last_error}\n```\n\n"
        f"> **Инструкция для Jules:**\n"
        f"> 1. Переключись в ветку `{branch}`.\n"
        f"> 2. Исправь код модуля `skills/{mod_name}.py` и тесты в папке `tests/` (`tests/test_{mod_name}.py` / `tests/test_{mod_name}_integration.py`).\n"
        f"> 3. Добейся успешного прохождения `python -m unittest discover -s tests` и открой Pull Request в `main`.\n"
        f"> 4. **НЕ трогай `main.py`, `skills/EPIC.md` и `skills/LESSONS.md`** — это общие файлы, "
        f"в них постоянно пишет автономный цикл, и правки здесь почти гарантированно приведут "
        f"к конфликту при мерже. Если для фикса реально нужны изменения в `main.py` — опиши это "
        f"отдельным комментарием к issue вместо прямой правки."
    )
    payload = {"title": f"Jules Task: исправить сбой модуля {mod_name}", "body": body}
    try:
        res = requests.post(issue_url, headers=API_HEADERS, json=payload, timeout=10)
        if res.status_code in [200, 201]:
            issue_data = res.json()
            issue_number = issue_data.get("number")
            if issue_number:
                add_jules_label(issue_number)
            return issue_data.get("html_url", "")
        print(f"[!] Ошибка создания Issue (HTTP {res.status_code}): {res.text}")
    except Exception as e:
        print(f"[!] Ошибка запроса создания Issue: {e}")
    return ""

def add_jules_label(issue_number: int) -> bool:
    url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/issues/{issue_number}/labels")
    try:
        res = requests.post(url, headers=API_HEADERS, json={"labels": ["jules"]}, timeout=10)
        if res.status_code in [200, 201]:
            return True
        print(f"[!] Не удалось поставить лейбл jules на #{issue_number}")
        return False
    except Exception as e:
        print(f"[!] Ошибка добавления лейбла jules на #{issue_number}: {e}")
        return False

def reactivate_stuck_jules_issues() -> int:
    url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/issues")
    try:
        res = requests.get(url, headers=API_HEADERS, params={"state": "open", "per_page": 100}, timeout=10)
        if res.status_code != 200:
            return 0
        issues = [i for i in res.json() if i.get("title", "").startswith("Jules Task:")]
    except Exception:
        return 0

    reactivated = 0
    for issue in issues:
        number = issue.get("number")
        if not number:
            continue
        has_label = any(l.get("name") == "jules" for l in issue.get("labels", []))
        if has_label:
            del_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/issues/{number}/labels/jules")
            try:
                requests.delete(del_url, headers=API_HEADERS, timeout=10)
            except Exception:
                pass
        if add_jules_label(number):
            reactivated += 1
    return reactivated

def run_jules_babysitter():
    print("[+] Демон-нянька для Jules запущен.")
    while True:
        time.sleep(180)
        url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/issues")
        try:
            res = requests.get(url, headers=API_HEADERS, params={"state": "open", "per_page": 50}, timeout=10)
            if res.status_code != 200:
                continue

            issues = [i for i in res.json() if i.get("title", "").startswith("Jules Task:")]

            for issue in issues:
                num = issue.get("number")
                if not num:
                    continue

                c_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/issues/{num}/comments")
                c_res = requests.get(c_url, headers=API_HEADERS, timeout=10)

                if c_res.status_code == 200:
                    comments = c_res.json()
                    if not comments:
                        continue

                    last_comment = comments[-1]
                    c_id = last_comment.get("id")
                    body = last_comment.get("body", "").lower()

                    if c_id not in HANDLED_JULES_COMMENTS and (
                        "jules has failed" in body or "try again later by removing and re-adding" in body
                    ):
                        print(f"[*] Jules споткнулся в Issue #{num} (коммент #{c_id}). Перезапуск задачи...")
                        HANDLED_JULES_COMMENTS.add(c_id)

                        del_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/issues/{num}/labels/jules")
                        requests.delete(del_url, headers=API_HEADERS, timeout=10)

                        time.sleep(2)
                        add_jules_label(num)

        except Exception as e:
            print(f"[!] Ошибка няньки Jules: {e}")

def refresh_stuck_prs() -> tuple:
    list_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/pulls")
    try:
        res = requests.get(list_url, headers=API_HEADERS, params={"state": "open", "per_page": 50}, timeout=10)
        if res.status_code != 200:
            return 0, []
        pr_numbers = [p.get("number") for p in res.json() if p.get("number")]
    except Exception:
        return 0, []

    refreshed = 0
    dirty_urls = []
    for number in pr_numbers:
        detail_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/pulls/{number}")
        try:
            d = requests.get(detail_url, headers=API_HEADERS, timeout=10)
            if d.status_code != 200:
                continue
            pr_data = d.json()
            state = pr_data.get("mergeable_state")
        except Exception:
            continue

        if state == "behind":
            update_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/pulls/{number}/update-branch")
            try:
                r = requests.put(update_url, headers=API_HEADERS, timeout=10)
                if r.status_code in [200, 202]:
                    refreshed += 1
            except Exception:
                pass
        elif state == "dirty":
            dirty_urls.append(pr_data.get("html_url", f"#{number}"))

    return refreshed, dirty_urls

def cleanup_orphan_branches() -> int:
    branches_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/branches")
    prs_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/pulls")
    try:
        br_res = requests.get(branches_url, headers=API_HEADERS, params={"per_page": 100}, timeout=10)
        pr_res = requests.get(prs_url, headers=API_HEADERS, params={"state": "open", "per_page": 100}, timeout=10)
        if br_res.status_code != 200 or pr_res.status_code != 200:
            return 0
        branch_names = [b["name"] for b in br_res.json() if b["name"].startswith("unga-")]
        branches_with_pr = {pr["head"]["ref"] for pr in pr_res.json()}
    except Exception:
        return 0

    deleted = 0
    for name in branch_names:
        if name in branches_with_pr:
            continue
        commit_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/branches/{name}")
        try:
            c = requests.get(commit_url, headers=API_HEADERS, timeout=10)
            if c.status_code != 200:
                continue
            commit_date_str = c.json().get("commit", {}).get("commit", {}).get("committer", {}).get("date", "")
            commit_date = datetime.strptime(commit_date_str, "%Y-%m-%dT%H:%M:%SZ")
            if (datetime.utcnow() - commit_date).total_seconds() < 86400:
                continue
        except Exception:
            continue

        del_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{name}")
        try:
            r = requests.delete(del_url, headers=API_HEADERS, timeout=10)
            if r.status_code in [200, 204]:
                deleted += 1
        except Exception:
            pass
    return deleted

NOISE_PREFIXES = ["resilient_", "secure_", "clean_", "compressed_", "smart_", "global_", "mesh_"]
PENDING_CLEANUP_PLAN = []

def _normalize_skill_name(name: str) -> str:
    n = name
    changed = True
    while changed:
        changed = False
        for p in NOISE_PREFIXES:
            if n.startswith(p):
                n = n[len(p):]
                changed = True
    return n

def find_duplicate_skill_clusters() -> dict:
    url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/skills?ref=main")
    try:
        r = requests.get(url, headers=API_HEADERS, timeout=15)
        if r.status_code != 200:
            return {}
        files = [f["name"] for f in r.json() if f["name"].endswith(".py") and f["name"] != "__init__.py"]
    except Exception:
        return {}

    clusters = {}
    for fname in files:
        core = _normalize_skill_name(fname[:-3])
        clusters.setdefault(core, []).append(fname)
    return {k: v for k, v in clusters.items() if len(v) > 1}

def get_all_skill_sources() -> dict:
    url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/skills?ref=main")
    try:
        r = requests.get(url, headers=API_HEADERS, timeout=15)
        if r.status_code != 200:
            return {}
        files = [f["name"] for f in r.json() if f["name"].endswith(".py") and f["name"] != "__init__.py"]
    except Exception:
        return {}

    sources = {}
    for fname in files:
        code = get_file_content("main", f"skills/{fname}")
        if code:
            sources[fname[:-3]] = code
    return sources

def find_skill_dependents(target: str, sources: dict) -> list:
    pattern = re.compile(rf'(from\s+skills\.{re.escape(target)}\s+import|import\s+skills\.{re.escape(target)}\b)')
    return [name for name, code in sources.items() if name != target and pattern.search(code)]

def build_cleanup_plan() -> tuple:
    clusters = find_duplicate_skill_clusters()
    if not clusters:
        return "🧹 Дублей не найдено — репозиторий чист.", []

    per_cluster = {}
    tentative_losers = set()
    for core, files in sorted(clusters.items()):
        dated = []
        for fname in files:
            try:
                cr = requests.get(
                    clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/commits"),
                    headers=API_HEADERS, params={"path": f"skills/{fname}", "per_page": 1}, timeout=10
                )
                commits = cr.json() if cr.status_code == 200 else []
                date_str = commits[0]["commit"]["committer"]["date"] if commits else "1970-01-01T00:00:00Z"
            except Exception:
                date_str = "1970-01-01T00:00:00Z"
            dated.append((fname, date_str))
        dated.sort(key=lambda x: x[1], reverse=True)
        keep = dated[0][0]
        losers = [f for f, _ in dated[1:]]
        per_cluster[core] = {"keep": keep, "losers": losers}
        tentative_losers.update(f[:-3] for f in losers)

    sources = get_all_skill_sources()
    to_delete = []
    report_lines = []
    for core, info in per_cluster.items():
        keep, losers = info["keep"], info["losers"]
        safe_losers, protected_lines = [], []
        for fname in losers:
            base = fname[:-3]
            dependents = [d for d in find_skill_dependents(base, sources) if d not in tentative_losers]
            if dependents:
                protected_lines.append(f"    ⛔ {fname} НЕ трогаю — от него зависит: {', '.join(dependents)}")
            else:
                safe_losers.append(fname)

        to_delete.extend(safe_losers)
        report_lines.append(f"• <b>{html.escape(core)}</b>: оставляю <code>{html.escape(keep)}</code>, удаляю {len(safe_losers)} из {len(losers)}")
        report_lines.extend(protected_lines)

    report = "🧹 <b>План очистки дублей</b>\n━━━━━━━━━━━━━━━━━━━\n" + "\n".join(report_lines[:30])
    if len(report_lines) > 30:
        report += f"\n...и ещё {len(report_lines) - 30} строк"
    report += (
        f"\n\nВсего файлов на удаление: <b>{len(to_delete)}</b> (плюс их тесты). "
        "Реальные import-зависимости уже проверены и защищены — ⛔ выше показывает, что осталось нетронутым."
    )
    return report, to_delete

def execute_cleanup_plan(files_to_delete: list) -> int:
    deleted = 0
    for fname in files_to_delete:
        base = fname[:-3] if fname.endswith(".py") else fname
        for path in (f"skills/{fname}", f"tests/test_{base}.py", f"tests/test_{base}_integration.py"):
            info_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/{path}?ref=main")
            try:
                info = requests.get(info_url, headers=API_HEADERS, timeout=10)
                if info.status_code != 200:
                    continue
                sha = info.json().get("sha")
                del_res = requests.delete(
                    clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/{path}"),
                    headers=API_HEADERS,
                    json={"message": f"Чистка дублей: удаляю {path} [skip ci]", "sha": sha, "branch": "main"},
                    timeout=10
                )
                if del_res.status_code in [200, 201]:
                    deleted += 1
            except Exception:
                pass
    return deleted

# 6. АНТИЧИТ
def inspect_code_for_cheating(code: str, existing_skills: list, target_module: str) -> str:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Синтаксическая ошибка в коде: {e}"

    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            if node.name in existing_skills and node.name != target_module:
                return (
                    f"ЧИТЕРСТВО ОБНАРУЖЕНО: Объявлен фиктивный '{node.name}'! "
                    f"Запрещено создавать заглушки. Используй честный импорт: 'from skills.{node.name} import ...'"
                )
        if isinstance(node, ast.ExceptHandler):
            is_broad = False
            if node.type is None:
                is_broad = True
            elif isinstance(node.type, ast.Name) and node.type.id in ["Exception", "BaseException"]:
                is_broad = True

            if is_broad and len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                return (
                    "АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! "
                    "Обработай ошибку предсказуемо или пробрось наружу через raise."
                )
    return ""

# 7. МАНИФЕСТ И ПАМЯТЬ
LESSONS_PATH = "skills/LESSONS.md"
LESSONS_HEADER = "# Уроки Унги\n\nЭто файл, который бот пишет и читает сам.\n"
MAX_LESSONS_CHARS_IN_PROMPT = 4000
MAX_LESSONS_FILE_CHARS = 16000

EPIC_PATH = "skills/EPIC.md"
EPIC_HEADER = "# Текущий эпик Унги\n\nЭто многошаговая цель бота, которая живёт дольше одного цикла — тут видно, к чему бот идёт, а не только что он только что сделал.\n\nНет активного эпика — можно предложить новый.\n"

def get_epic_context() -> str:
    content = get_file_content("main", EPIC_PATH)
    return content if content else "Нет активного эпика — можно предложить новый."

def update_epic_file(branch: str, decision: dict) -> None:
    status = decision.get("epic_status", "none")
    if status not in ("start_new", "continue", "complete"):
        return

    title = (decision.get("epic_title") or "Без названия").strip()
    step_note = (decision.get("epic_step_note") or "").strip()
    mod_name = decision.get("module_name", "?")

    if status == "start_new":
        content = f"# Текущий эпик Унги\n\n## {title}\n\n- {mod_name}"
        content += f": {step_note}\n" if step_note else ": первый шаг эпика\n"
    else:
        existing = get_file_content(branch, EPIC_PATH) or get_file_content("main", EPIC_PATH) or EPIC_HEADER
        line = f"- {mod_name}: {step_note}" if step_note else f"- {mod_name}: шаг эпика выполнен"
        if status == "complete":
            line += "  ✅ ЭПИК ЗАВЕРШЁН"
        content = existing.rstrip() + "\n" + line + "\n"
        if status == "complete":
            content += "\nНет активного эпика — можно предложить новый.\n"

    commit_file_to_branch(branch, EPIC_PATH, content, f"Эпик «{title}»: {status}")

_MANIFEST_CACHE = {"data": {}, "fingerprint": None}

def get_skills_manifest(force_refresh: bool = False) -> dict:
    dir_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/skills?ref=main")
    try:
        dir_res = requests.get(dir_url, headers=API_HEADERS, timeout=10)
        if dir_res.status_code != 200:
            return _MANIFEST_CACHE["data"]
        listing = dir_res.json()
    except Exception:
        return _MANIFEST_CACHE["data"]

    py_files = [f for f in listing if f["name"].endswith(".py") and f["name"] != "__init__.py"]
    fingerprint = "|".join(sorted(f"{f['name']}:{f.get('sha', '')}" for f in py_files))

    if not force_refresh and fingerprint == _MANIFEST_CACHE["fingerprint"] and _MANIFEST_CACHE["data"]:
        return _MANIFEST_CACHE["data"]

    manifest = {}
    for f_info in py_files:
        f_name = f_info["name"]
        mod_key = f_name[:-3]
        code = get_file_content("main", f"skills/{f_name}")
        if not code:
            continue
        signatures = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                    args = [a.arg for a in node.args.args]
                    ret = f" -> {ast.unparse(node.returns)}" if getattr(node, "returns", None) else ""
                    doc = ast.get_docstring(node)
                    doc_snippet = f" | {doc.splitlines()[0][:60]}" if doc else ""
                    signatures.append(f"def {node.name}({', '.join(args)}){ret}{doc_snippet}")
                elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                    methods = []
                    init_node = next((m for m in node.body if isinstance(m, ast.FunctionDef) and m.name == "__init__"), None)
                    if init_node:
                        init_args = [a.arg for a in init_node.args.args if a.arg != "self"]
                        methods.append(f"__init__({', '.join(init_args)})")
                    for m in node.body:
                        if isinstance(m, ast.FunctionDef) and not m.name.startswith("_"):
                            m_args = [a.arg for a in m.args.args]
                            m_ret = f" -> {ast.unparse(m.returns)}" if getattr(m, "returns", None) else ""
                            methods.append(f"{m.name}({', '.join(m_args)}){m_ret}")
                    doc = ast.get_docstring(node)
                    doc_snippet = f" | {doc.splitlines()[0][:60]}" if doc else ""
                    signatures.append(f"class {node.name}{doc_snippet} [методы: {', '.join(methods)}]")
        except Exception:
            pass
        manifest[mod_key] = signatures if signatures else ["нет сигнатур"]

    _MANIFEST_CACHE["data"] = manifest
    _MANIFEST_CACHE["fingerprint"] = fingerprint
    return manifest

MAX_MANIFEST_PROMPT_CHARS = 6000

def manifest_for_prompt(manifest: dict, always_full: list = None) -> str:
    always_full = set(always_full or [])
    full = json.dumps(manifest, indent=2, ensure_ascii=False)
    if len(full) <= MAX_MANIFEST_PROMPT_CHARS:
        return full

    compact = {k: (v if k in always_full else (v[:1] if v else [])) for k, v in manifest.items()}
    compact_json = json.dumps(compact, indent=2, ensure_ascii=False)
    if len(compact_json) <= MAX_MANIFEST_PROMPT_CHARS:
        return compact_json

    names_only = {k: (v if k in always_full else "...") for k, v in manifest.items()}
    return json.dumps(names_only, ensure_ascii=False)

def get_lessons_context() -> str:
    content = get_file_content("main", LESSONS_PATH)
    if not content:
        return "Пока нет накопленных уроков."
    if len(content) > MAX_LESSONS_CHARS_IN_PROMPT:
        return "...(старые записи обрезаны)...\n" + content[-MAX_LESSONS_CHARS_IN_PROMPT:]
    return content

def _build_lesson_entry(mod_name: str, action: str, rounds: int, cheats_caught: list, last_error: str, status_line: str) -> str:
    entry_lines = [f"\n## {mod_name} ({action}) — раундов: {rounds}"]
    if cheats_caught:
        entry_lines.append(f"- Античит поймал: {'; '.join(cheats_caught)}")
    if last_error:
        snippet = next((l for l in reversed(last_error.strip().splitlines()) if l.strip()), "")
        if snippet:
            entry_lines.append(f"- Последняя ошибка перед фиксом: {snippet[:300]}")
    entry_lines.append(f"- Статус: {status_line}")
    return "\n".join(entry_lines)

def _merge_lessons_text(existing: str, entry: str) -> str:
    updated = existing.rstrip() + "\n" + entry + "\n"
    if len(updated) > MAX_LESSONS_FILE_CHARS:
        updated = LESSONS_HEADER + "\n...(старые уроки обрезаны)...\n" + updated[-MAX_LESSONS_FILE_CHARS:]
    return updated

def append_lesson_to_branch(branch: str, mod_name: str, action: str, rounds: int, cheats_caught: list, last_error: str = "") -> None:
    existing = get_file_content(branch, LESSONS_PATH) or get_file_content("main", LESSONS_PATH) or LESSONS_HEADER
    entry = _build_lesson_entry(mod_name, action, rounds, cheats_caught, last_error, "успешно прошёл тесты и влит в main")
    commit_file_to_branch(branch, LESSONS_PATH, _merge_lessons_text(existing, entry), f"Урок: {mod_name}")

def append_failure_lesson_directly(mod_name: str, action: str, rounds: int, cheats_caught: list, last_error: str = "") -> None:
    base_sha = get_main_sha()
    if not base_sha:
        return

    note_branch = f"unga-lesson-{mod_name}-{int(time.time())}"
    if not prepare_branch(note_branch, base_sha):
        return

    existing = get_file_content("main", LESSONS_PATH) or LESSONS_HEADER
    entry = _build_lesson_entry(mod_name, action, rounds, cheats_caught, last_error, "ПРОВАЛЕН Унгой, передан на эскалацию")
    commit_file_to_branch(note_branch, LESSONS_PATH, _merge_lessons_text(existing, entry), f"Урок (сбой): {mod_name}")

    m_res = requests.post(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/merges"), headers=API_HEADERS, json={
        "base": "main", "head": note_branch, "commit_message": f"Урок из сбоя: {mod_name}"
    }, timeout=10)

    if m_res.status_code in [200, 201, 204]:
        requests.delete(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{note_branch}"), headers=API_HEADERS)

# 8. ПЛАНИРОВАНИЕ И ГЕНЕРАЦИЯ
FILLER_TOKENS = {
    "resilient", "secure", "smart", "clean", "compressed",
    "robust", "hardened", "autonomous", "advanced", "enhanced", "safe",
    "optimized", "optimised", "reliable", "improved", "final", "omega",
    "singularity", "ultimate", "core", "pro", "v1", "v2", "v3", "v4", "v5",
    "v6", "v7", "v8", "v9", "v10", "v11", "v12"
}

def _core_tokens(name: str) -> set:
    tokens = re.split(r'[_\d]+', name.lower())
    return {t for t in tokens if t and t not in FILLER_TOKENS}

def find_near_duplicate(module_name: str, manifest: dict) -> str:
    new_core = _core_tokens(module_name)
    if not new_core:
        return ""
    best_match, best_overlap = "", 0.0
    for existing_name in manifest.keys():
        existing_core = _core_tokens(existing_name)
        if not existing_core:
            continue
        overlap = len(new_core & existing_core) / len(new_core | existing_core)
        if overlap > best_overlap:
            best_match, best_overlap = existing_name, overlap
    return best_match if best_overlap >= 0.6 else ""

def dream_action(manifest: dict, lessons: str, epic: str, manual_prompt: str = "") -> dict:
    if manual_prompt:
        prompt = (
            f"Пользователь дал прямое ТЗ: '{manual_prompt}'\n"
            f"МАНИФЕСТ СУЩЕСТВУЮЩИХ МОДУЛЕЙ:\n{manifest_for_prompt(manifest)}\n\n"
            "Сформируй спецификацию нового модуля под эту задачу.\n"
            "Верни СТРОГО JSON:\n"
            "{\n"
            '  "action": "create",\n'
            '  "module_name": "латинское_имя_без_py",\n'
            '  "description": "суть модуля",\n'
            '  "class_or_func": "сигнатуры функций/классов",\n'
            '  "composed_of": [],\n'
            '  "epic_status": "none",\n'
            '  "epic_title": "",\n'
            '  "epic_step_note": ""\n'
            "}"
        )
    else:
        skill_names = list(manifest.keys())
        can_compose = len(skill_names) >= 2
        compose_hint = (
            "3. 'compose': Скомбинируй РОВНО 2 (максимум 3) существующих модуля из манифеста для новой задачи. "
            "Заполни 'composed_of' списком их имён.\n"
        ) if can_compose else ""
        prompt = (
            "Ты — Стратег-Паразит. Цель — не просто плодить модули, а РЕАЛЬНО развиваться: выстраивать "
            "многошаговые направления, где каждая задача продвигает что-то большее, чем она сама.\n\n"
            f"УЖЕ СОЗДАННЫЕ МОДУЛИ:\n{manifest_for_prompt(manifest)}\n\n"
            f"УРОКИ:\n{lessons}\n\n"
            f"ТЕКУЩИЙ ЭПИК (многошаговая цель дольше одного цикла):\n{epic}\n\n"
            "ПРАВИЛО ПРО ЭПИК:\n"
            "- Если эпик активен — ОБЯЗАН выбрать действие, которое реально его продвигает, а не постороннюю "
            "задачу. Заполни 'epic_status': 'continue', или 'complete', если этим шагом эпик закрыт целиком.\n"
            "- Если эпика нет или он только что завершён — можешь предложить НОВЫЙ: короткое, амбициозное, "
            "реалистичное направление на 3-6 будущих циклов (например: 'Система мониторинга: RSS → чистка "
            "текста → кэш → дайджест в Telegram'). Заполни 'epic_status': 'start_new' и 'epic_title'.\n"
            "- Если явно нечего предложить в качестве эпика — 'epic_status': 'none'.\n\n"
            "ДЕЙСТВИЯ ДЛЯ ТЕКУЩЕГО ШАГА:\n"
            "1. 'create': НОВАЯ концепция, которой реально нет в списке модулей.\n"
            "2. 'refactor': module_name ДОЛЖЕН БУКВАЛЬНО СОВПАДАТЬ с уже существующим именем из манифеста "
            "выше. ЗАПРЕЩЕНО придумывать 'улучшенную' версию с новым именем "
            "(например 'secure_' + старое имя, 'resilient_' + старое имя) — это не рефакторинг, "
            "а дубликат, раздувающий репозиторий и CI. Если хочешь улучшить X — module_name='X', не 'secure_X'.\n"
            f"{compose_hint}\n"
            "ТРЕБОВАНИЯ: Python 3.11, requests, beautifulsoup4 (bs4).\n"
            "Верни СТРОГО JSON:\n"
            "{\n"
            '  "action": "create" или "refactor" или "compose",\n'
            '  "module_name": "латинское_имя_без_py",\n'
            '  "description": "суть модуля",\n'
            '  "class_or_func": "сигнатуры функций/классов",\n'
            '  "composed_of": ["модуль1", "модуль2"],\n'
            '  "epic_status": "start_new" | "continue" | "complete" | "none",\n'
            '  "epic_title": "название эпика (пусто, если epic_status=none)",\n'
            '  "epic_step_note": "как именно эта задача продвигает эпик"\n'
            "}"
        )

    raw = ask_gemini(prompt, json_mode=True)
    try:
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        clean_raw = json_match.group(0) if json_match else raw
        data = json.loads(clean_raw)
        mod = re.sub(r'[^a-zA-Z0-9_]', '', data.get("module_name", "").lower())
        if not mod:
            raise ValueError("Empty module name")
        data["module_name"] = mod

        if mod not in manifest:
            duplicate = ""
            for existing in manifest:
                if existing != mod and (existing in mod or mod in existing):
                    duplicate = existing
                    break
            if not duplicate:
                duplicate = find_near_duplicate(mod, manifest)
            if duplicate:
                print(f"[!] Инфляция имён: '{mod}' — вариация '{duplicate}'. Рефакторю оригинал вместо дубликата.")
                mod = duplicate
                data["module_name"] = mod
                data["action"] = "refactor"

        if data.get("action") == "refactor" and mod not in manifest:
            data["action"] = "create"

        composed_of_raw = data.get("composed_of") or []
        composed_of = [c for c in composed_of_raw if isinstance(c, str) and c in manifest]
        if data.get("action") == "compose" and len(composed_of) < 2:
            data["action"] = "create"
            composed_of = []
        elif data.get("action") != "compose":
            composed_of = []

        data["composed_of"] = composed_of
        if data.get("epic_status") not in ("start_new", "continue", "complete", "none"):
            data["epic_status"] = "none"
        return data
    except Exception as e:
        print(f"[!] Ошибка парсинга Стратега: {e}, fallback")
        return {
            "action": "create",
            "module_name": f"extractor_tool_{int(time.time())}",
            "description": "Модуль извлечения метаданных из разметки",
            "class_or_func": "parse_meta(html: str) -> dict",
            "composed_of": [],
            "epic_status": "none",
            "epic_title": "",
            "epic_step_note": ""
        }

def _compose_context(task: dict) -> str:
    composed_of = task.get("composed_of") or []
    if not composed_of:
        return ""
    return f"\nЭТО КОМПОЗИЦИЯ: модуль ОБЯЗАН импортировать и использовать существующие навыки {composed_of}.\n"

def architect_write_hard_tests(task: dict, manifest: dict, lessons: str, existing_code: str = "", error_log: str = "") -> str:
    context_code = f"КОД ДО РЕФАКТОРИНГА:\n{existing_code}\n" if existing_code else ""
    context_stagnation = f"\nПОВТОРЯЮЩАЯСЯ ОШИБКА ТЕСТА:\n{error_log}\n" if error_log else ""
    prompt = (
        "Ты — Архитектор-Инквизитор. Напиши ЮНИТ-тесты unittest.\n"
        f"Задача: {task['action']} модуля skills/{task['module_name']}.py\n"
        f"Описание: {task['description']}\n"
        f"{context_code}{_compose_context(task)}{context_stagnation}\n"
        f"СИГНАТУРЫ И ТИПЫ:\n{manifest_for_prompt(manifest, always_full=task.get('composed_of'))}\n\n"
        "СТРОГИЕ ПРАВИЛА:\n"
        "1. Библиотеки: standard lib, unittest, unittest.mock, requests, bs4.\n"
        "2. Запрещено вешать `@patch` над методами! Только `with patch(...) as mock:` внутри метода!\n"
        "3. Валидация возвращает bool: проверяй `assertTrue(res)` или `assertFalse(res)`. НЕ ПИШИ `res[0]`!\n"
        "4. Ошибки: ждёшь падения — используй `with self.assertRaises(...)`. Без assertRaises функция должна вернуть False, а не падать!\n"
        "5. Моки потоков: если код вызывает `.read()`, подсовывай `io.BytesIO(b'...')`, а не dict!\n"
        "6. Верни ТОЛЬКО валидный код тестов Python без markdown."
    )
    return ask_gemini(prompt)

def architect_write_integration_test(task: dict, manifest: dict, lessons: str, existing_code: str = "") -> str:
    context_code = f"КОД ДО РЕФАКТОРИНГА:\n{existing_code}\n" if existing_code else ""
    prompt = (
        "Ты — Архитектор. Напиши ИНТЕГРАЦИОННЫЙ тест (без моков между навыками).\n"
        f"Модуль: skills/{task['module_name']}.py\n"
        f"Описание: {task['description']}\n"
        f"{context_code}{_compose_context(task)}\n"
        f"СИГНАТУРЫ:\n{manifest_for_prompt(manifest, always_full=task.get('composed_of'))}\n\n"
        "ПРАВИЛА: Смотри на возвращаемые типы (str, bool). Импортируй ТОЛЬКО существующие имена. Вызывай создаваемый модуль. Без markdown."
    )
    return ask_gemini(prompt)

def unga_implement_hardened(task: dict, unit_test_code: str, integration_test_code: str, manifest: dict, existing_code: str = "", error_log: str = "") -> str:
    context_err = f"ОШИБКА С ПРОШЛОГО РАУНДА:\n{error_log}\n" if error_log else ""
    context_base = f"БАЗОВЙ КОД:\n{existing_code}\n" if existing_code else ""
    prompt = (
        "Ты — Унга, кодер. Подчинись ОБОИМ наборам тестов Архитектора.\n"
        f"Модуль: skills/{task['module_name']}.py\n"
        f"Цель: {task['description']}\n\n"
        f"{context_base}{_compose_context(task)}"
        f"ЮНИТ-ТЕСТЫ:\n{unit_test_code}\n\n"
        f"ИНТЕГРАЦИОННЫЕ ТЕСТЫ:\n{integration_test_code}\n\n"
        f"{context_err}\n"
        "ПРАВИЛА: Валидация возвращает чистый bool. Исключения бросай только если в тестах есть assertRaises. "
        "Мерж словарей через update или {**a, **b}. Без 'except Exception: pass'. Верни только чистый Python-код."
    )
    return ask_gemini(prompt)

# 9. БОЕВОЙ ЦИКЛ С АВТОЭВРИСТИКОЙ И ЭСКАЛАЦИЕЙ НА JULES
def write_epic_smoke_test(epic_title: str, epic_body: str, manifest: dict) -> str:
    prompt = (
        "Ты пишешь ОДНОРАЗОВУЮ ПРАКТИЧЕСКУЮ ПРОВЕРКУ завершённого эпика — не часть постоянного "
        "набора регрессионных тестов, а честную демонстрацию, что заявленная способность реально "
        "работает в реальном мире, а не только против моков и локальных серверов.\n\n"
        f"Эпик: {epic_title}\n"
        f"Контекст эпика (файл EPIC.md):\n{epic_body}\n\n"
        f"ДОСТУПНЫЕ МОДУЛИ (используй их РЕАЛЬНО, честным импортом из skills.*, без моков):\n"
        f"{manifest_for_prompt(manifest)}\n\n"
        "ПРАВИЛА:\n"
        "1. ЭТО ЕДИНСТВЕННЫЙ случай, когда реальная сеть РАЗРЕШЕНА и ОБЯЗАТЕЛЬНА — сходи на реальный, "
        "стабильный, общеизвестный публичный сайт/RSS-фид, подходящий по смыслу эпику (например: "
        "hnrss.org, rss-фид крупного новостного сайта, example.com) — что-то, что не требует "
        "авторизации и не пропадёт завтра.\n"
        "2. Заведи один мягкий повтор (retry) на случай единичного сетевого сбоя, но не больше "
        "2 попыток — это не постоянный сьют, зависать не должен.\n"
        "3. Тест должен явно печатать (print) реальные полученные данные (заголовок статьи, "
        "фрагмент текста и т.п.), а не просто OK/FAIL — чтобы в логах было видно живое доказательство.\n"
        "4. Оформи как unittest.TestCase с одним-двумя показательными тестами.\n"
        "5. Верни ТОЛЬКО валидный Python-код файла без markdown."
    )
    return ask_gemini(prompt)

def run_epic_smoke_test(epic_title: str, manifest: dict) -> None:
    epic_body = get_epic_context()
    print(f"\n[~] ПРАКТИЧЕСКАЯ ПРОВЕРКА ЭПИКА: '{epic_title}'")
    send_tg(f"🧪 Эпик <b>{html.escape(epic_title)}</b> завершён — проверяю на практике, в реальном мире...")

    branch = f"unga-epic-smoke-{int(time.time())}"
    if not prepare_branch(branch, get_main_sha()):
        print("[-] Практическая проверка: не удалось подготовить ветку.")
        return

    smoke_path = "tests/test_epic_smoke.py"
    last_error = ""
    passed = False
    run_id = None

    for attempt in range(1, 3):
        smoke_code = write_epic_smoke_test(epic_title, epic_body, manifest)
        commit_msg = f"Практическая проверка эпика «{epic_title}» #{attempt}"
        target_sha = commit_file_to_branch(branch, smoke_path, smoke_code, commit_msg)
        print(f"[*] Практическая проверка закоммичена (SHA: {target_sha[:7]}), раунд #{attempt}...")
        passed, run_id = watch_arena_by_sha(target_sha)
        if passed:
            break
        last_error = extract_clean_test_traceback(run_id)
        print(f"[!] Практическая проверка провалилась в реальных условиях:\n{last_error}\n")

    if passed:
        send_tg(f"✅ <b>Практическая проверка пройдена</b>\n━━━━━━━━━━━━━━━━━━━\n🏁 Эпик «{html.escape(epic_title)}» подтверждён в реальном мире!")
        requests.delete(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{branch}"), headers=API_HEADERS)
    else:
        issue_title_hint = re.sub(r'[^a-zA-Z0-9_]', '_', epic_title.lower())[:40] or "epic"
        issue_url = escalate_to_github_issue(
            issue_title_hint,
            f"Практическая проверка завершённого эпика «{epic_title}» провалилась в реальных условиях "
            "(юнит- и интеграционные тесты при этом прошли).",
            last_error,
            branch
        )
        send_tg(
            f"❌ <b>Практическая проверка провалена</b>\n━━━━━━━━━━━━━━━━━━━\n"
            f"🏁 Эпик «{html.escape(epic_title)}»\n"
            "Юнит- и интеграционные тесты были зелёными, но в реальных условиях что-то не работает.\n"
            "🚨 Передано Jules.",
            buttons=tg_issue_button(issue_url)
        )

def delete_repo_file(path: str, message: str, branch: str = "main") -> bool:
    file_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/{path}?ref={branch}")
    try:
        info = requests.get(file_url, headers=API_HEADERS, timeout=10)
        if info.status_code != 200:
            return True
        sha = info.json().get("sha")
        res = requests.delete(
            clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/{path}"),
            headers=API_HEADERS,
            json={"message": message, "sha": sha, "branch": branch},
            timeout=10
        )
        return res.status_code in [200, 204]
    except Exception:
        return False

def find_poisoning_import_error(error_text: str) -> str:
    m = re.search(r"Failed to import test module:\s*(\S+)", error_text or "")
    return m.group(1).strip() if m else ""

def check_main_health() -> tuple:
    url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/actions/runs")
    try:
        r = requests.get(url, headers=API_HEADERS, params={"branch": "main", "per_page": 1}, timeout=10)
        if r.status_code != 200:
            return True, "", None
        runs = r.json().get("workflow_runs", [])
        if not runs or runs[0].get("status") != "completed" or runs[0].get("conclusion") == "success":
            return True, "", None
        run_id = runs[0].get("id")
        return False, extract_clean_test_traceback(run_id), run_id
    except Exception:
        return True, "", None

def bulk_quarantine_orphaned_tests() -> list:
    """
    Каждый test_*.py у нас всегда назван по имени своего модуля (test_X.py или
    test_X_integration.py для skills/X.py). Если X давно удалён (например, через
    /cleanup или просто заброшен посреди истории с раздуванием имён), а тест
    остался — при сборе тестов он падает на импорте и ломает ВЕСЬ прогон для
    абсолютно любой задачи. Реактивный карантин по одному файлу за раунд (через
    полный прогон CI на каждый) не масштабируется, если таких сирот сотни — это
    именно то, что случилось. Чистим всё разом, статически, без единого прогона CI:
    просто сверяем имя теста со списком реально существующих модулей.
    """
    url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents?ref=main")
    try:
        r = requests.get(url, headers=API_HEADERS, timeout=15)
        if r.status_code != 200:
            return []
        test_files = [f["name"] for f in r.json() if f["name"].startswith("test_") and f["name"].endswith(".py")]
    except Exception:
        return []

    manifest = get_skills_manifest()
    existing = set(manifest.keys())

    orphaned = []
    for fname in test_files:
        base = fname[:-3][len("test_"):]
        if base.endswith("_integration"):
            base = base[:-len("_integration")]
        if base not in existing:
            orphaned.append(fname)

    deleted = []
    for fname in orphaned:
        if delete_repo_file(fname, f"Массовый карантин: skills/{fname} давно удалён, тест-сирота больше не нужен [skip ci]"):
            deleted.append(fname)
    return deleted

def heal_main_if_poisoned() -> bool:
    healthy, error_text, run_id = check_main_health()
    if healthy:
        return False

    broken_module = find_poisoning_import_error(error_text)
    if broken_module:
        path = f"{broken_module}.py"
        if delete_repo_file(path, f"Карантин: {path} не импортируется и блокирует ВСЕ мутации [skip ci]"):
            print(f"[!] main был отравлен нерабочим тестом {path} — удалён в карантин.")
            send_tg(
                f"🧟 <b>Уборка мусора</b>\n━━━━━━━━━━━━━━━━━━━\n"
                f"Файл <code>{path}</code> не мог импортироваться и ломал CI. Удалил его. Идём дальше."
            )
            return True

    print(f"[!] main сломан, но не тем паттерном, который я умею чинить сам:\n{error_text[:500]}")
    send_tg(
        "🧟 <b>main сломан, авточинка не справилась</b>\n━━━━━━━━━━━━━━━━━━━\n"
        f"<pre>{html.escape(error_text[:500])}</pre>\n"
        "Пока это не поправить руками (или через Jules), новые мутации будут проваливаться."
    )
    return False

def is_jules_working_on(mod_name: str) -> bool:
    """
    Проверяет, занят ли Jules модулем прямо сейчас.
    Возвращает False, если Jules уже закончил работу (открыл PR) или сдох.
    """
    url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/issues")
    try:
        res = requests.get(url, headers=API_HEADERS, params={"state": "open", "per_page": 30}, timeout=10)
        if res.status_code != 200:
            return False

        for issue in res.json():
            if "pull_request" in issue:
                continue
            if not issue.get("title", "").startswith(f"Jules Task: исправить сбой модуля {mod_name}"):
                continue

            num = issue.get("number")
            c_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/issues/{num}/comments")
            c_res = requests.get(c_url, headers=API_HEADERS, timeout=10)
            if c_res.status_code != 200:
                return True

            comments = c_res.json()
            comments_text = " ".join([c.get("body", "").lower() for c in comments])

            if "ready for a review" in comments_text or "a pr has been created" in comments_text:
                return False

            if "jules has failed" in comments_text:
                return False

            if "is on it" in comments_text:
                created_at = datetime.strptime(issue["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                if (datetime.utcnow() - created_at).total_seconds() < 10800:
                    return True

    except Exception:
        pass
    return False

def run_evolution_cycle():
    print("\n==========================================")
    print("      ПИТЕКАНТРОП: БЕЗОПАСНЫЙ ЦИКЛ CI     ")
    print("==========================================")

    print("[~] Массовая чистка тестов-сирот (без единого прогона CI)...")
    orphan_tests = bulk_quarantine_orphaned_tests()
    if orphan_tests:
        print(f"[*] Удалено тестов-сирот: {len(orphan_tests)}")
        preview = ", ".join(orphan_tests[:10])
        if len(orphan_tests) > 10:
            preview += f" ...и ещё {len(orphan_tests) - 10}"
        send_tg(f"🧹 <b>Массовый карантин тестов-сирот</b>\n━━━━━━━━━━━━━━━━━━━\nУдалено: <b>{len(orphan_tests)}</b>\n<code>{html.escape(preview)}</code>")

    print("[~] Проверка здоровья main...")
    if heal_main_if_poisoned():
        print("[*] main вылечен в этом же проходе — продолжаю цикл на свежей базе.")

    print("[~] Профилактика: обновляю отстающие PR от main, чищу мусорные ветки...")
    refreshed, dirty_urls = refresh_stuck_prs()
    orphans_deleted = cleanup_orphan_branches()
    if refreshed or orphans_deleted:
        print(f"[*] Обновлено PR: {refreshed}, удалено мусорных веток: {orphans_deleted}")
    if dirty_urls:
        buttons = [[{"text": f"🔗 Конфликт в PR #{u.rstrip('/').split('/')[-1]}", "url": u}] for u in dirty_urls[:5]]
        send_tg(
            f"⚠️ <b>Настоящие конфликты в {len(dirty_urls)} PR</b>\n━━━━━━━━━━━━━━━━━━━\n"
            "Автоматическое обновление не спасает — нужна ручная (или Jules-) правка.",
            buttons=buttons
        )

    manifest = get_skills_manifest()
    skills_list = list(manifest.keys())
    lessons = get_lessons_context()
    epic = get_epic_context()

    manual_task = MANUAL_TASK_QUEUE.pop(0) if MANUAL_TASK_QUEUE else ""
    if manual_task:
        print(f"[!] ВЗЯТА РУЧНАЯ ЗАДАЧА ИЗ TELEGRAM: {manual_task}")
        send_tg(f"⚙️ <b>Питекантроп начал сборку:</b>\n<i>{html.escape(manual_task)}</i>")

    decision = dream_action(manifest, lessons, epic, manual_prompt=manual_task)
    mod_name = decision["module_name"]
    action = decision.get("action", "create")
    print(f"[+] Действие: {action.upper()} для '{mod_name}' — {decision.get('description')}")

    if is_jules_working_on(mod_name):
        msg = f"⏳ Модуль <code>{mod_name}</code> сейчас в реанимации у Jules. Пропускаю цикл, чтобы не затереть его ветку."
        print(f"[*] {msg}")
        send_tg(msg)
        return

    current_code = get_file_content("main", f"skills/{mod_name}.py") or ""

    test_code = architect_write_hard_tests(decision, manifest, lessons, existing_code=current_code)
    integration_test_code = architect_write_integration_test(decision, manifest, lessons, existing_code=current_code)

    branch = f"unga-{action}-{mod_name}"
    if not prepare_branch(branch, get_main_sha()):
        print("[-] Ошибка подготовки ветки.")
        return

    test_path = f"tests/test_{mod_name}.py"
    integration_test_path = f"tests/test_{mod_name}_integration.py"
    skill_path = f"skills/{mod_name}.py"

    commit_file_to_branch(branch, "skills/__init__.py", "# unga package\n", "Init package [skip ci]")
    commit_file_to_branch(branch, "tests/__init__.py", "# unga tests package\n", "Init tests [skip ci]")
    commit_file_to_branch(branch, test_path, test_code, f"Юнит-тесты для {mod_name} [skip ci]")
    commit_file_to_branch(branch, integration_test_path, integration_test_code, f"Интеграционные тесты для {mod_name} [skip ci]")

    impl_code = unga_implement_hardened(decision, test_code, integration_test_code, manifest, existing_code=current_code)

    attempts = 1
    rounds_used = 0
    passed = False
    run_id = None
    cheats_caught = []
    last_error = ""
    prev_error_signature = None
    stagnant_hits = 0
    tests_regenerated = False
    MAX_ATTEMPTS = 4
    MAX_POISON_RETRIES = 5
    poison_retries = 0
    poison_quarantined = []

    while attempts <= MAX_ATTEMPTS:
        rounds_used = attempts
        cheat_err = inspect_code_for_cheating(impl_code, skills_list, mod_name)
        if cheat_err:
            cheats_caught.append(cheat_err[:200])
            impl_code = unga_implement_hardened(decision, test_code, integration_test_code, manifest, existing_code=impl_code, error_log=cheat_err)
            attempts += 1
            continue

        target_sha = commit_file_to_branch(branch, skill_path, impl_code, f"Реализация #{attempts} для {mod_name}")
        passed, run_id = watch_arena_by_sha(target_sha)

        if passed:
            break

        last_error = extract_clean_test_traceback(run_id)

        poison_module = find_poisoning_import_error(last_error)
        own_test_names = {test_path[:-3], integration_test_path[:-3]}
        if poison_module and poison_module not in own_test_names and poison_retries < MAX_POISON_RETRIES:
            poison_retries += 1
            print(f"[!] Отравляющий файл {poison_module}.py не имеет отношения к '{mod_name}' — карантин ({poison_retries}/{MAX_POISON_RETRIES}) вместо правки своего кода.")
            if delete_repo_file(f"{poison_module}.py", f"Карантин: {poison_module}.py блокировал задачу {mod_name} [skip ci]", branch=branch):
                poison_quarantined.append(f"{poison_module}.py")
                continue
        elif poison_module and poison_retries >= MAX_POISON_RETRIES:
            print(f"[!] Потолок карантина ({MAX_POISON_RETRIES}) исчерпан для '{mod_name}' — похоже, сирот в репозитории намного больше, чем ожидалось. Останавливаюсь и сообщаю, вместо бесконечного цикла.")
            send_tg(
                f"🧟 <b>Карантин уткнулся в потолок</b>\n━━━━━━━━━━━━━━━━━━━\n"
                f"Для <code>{mod_name}</code> подряд нашлось {poison_retries}+ левых сломанных тестов "
                f"({', '.join(poison_quarantined[:8])}{'...' if len(poison_quarantined) > 8 else ''}). "
                "Похоже, сирот в репозитории куда больше, чем предполагалось — стоит запустить полную "
                "чистку вручную, а не полагаться на реактивный карантин."
            )
            break

        if poison_quarantined:
            send_tg(f"🧟 Карантин по ходу задачи <code>{mod_name}</code>: убрано {len(poison_quarantined)} посторонних сломанных тестов, повторяю раунд.")
            poison_quarantined = []

        error_signature = re.sub(r'\d+', '#', last_error)[-500:].strip()
        if prev_error_signature is not None and error_signature == prev_error_signature:
            stagnant_hits += 1
        else:
            stagnant_hits = 0
        prev_error_signature = error_signature

        if stagnant_hits >= 1 and not tests_regenerated and attempts < MAX_ATTEMPTS:
            test_code = architect_write_hard_tests(decision, manifest, lessons, existing_code=impl_code, error_log=last_error)
            integration_test_code = architect_write_integration_test(decision, manifest, lessons, existing_code=impl_code)
            commit_file_to_branch(branch, test_path, test_code, "Перегенерация юнит-тестов [skip ci]")
            commit_file_to_branch(branch, integration_test_path, integration_test_code, "Перегенерация интеграционных тестов [skip ci]")
            tests_regenerated = True
            stagnant_hits = 0

        impl_code = unga_implement_hardened(decision, test_code, integration_test_code, manifest, existing_code=impl_code, error_log=last_error)
        attempts += 1

    if passed:
        append_lesson_to_branch(branch, mod_name, action, rounds_used, cheats_caught, last_error)
        update_epic_file(branch, decision)
        m_res = requests.post(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/merges"), headers=API_HEADERS, json={
            "base": "main", "head": branch, "commit_message": f"ЭВОЛЮЦИЯ: Вливание skills/{mod_name}.py"
        }, timeout=10)

        if m_res.status_code in [200, 201, 204]:
            requests.delete(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{branch}"), headers=API_HEADERS)
            epic_line = ""
            if decision.get("epic_status") == "start_new":
                epic_line = f"\n\n🧭 <b>Новый эпик:</b> {html.escape(decision.get('epic_title', ''))}"
            elif decision.get("epic_status") == "continue":
                epic_line = f"\n\n🧭 <b>Продвигает эпик:</b> {html.escape(decision.get('epic_step_note', ''))}"
            elif decision.get("epic_status") == "complete":
                epic_line = f"\n\n🏁 <b>Эпик завершён:</b> {html.escape(decision.get('epic_title', ''))}"
            send_tg(
                f"✅ <b>Навык готов</b>\n━━━━━━━━━━━━━━━━━━━\n"
                f"<code>{mod_name}</code>\n"
                f"📝 {html.escape(decision.get('description', ''))}\n"
                f"🎯 Раундов: {rounds_used}"
                f"{epic_line}"
            )
            if decision.get("epic_status") == "complete":
                fresh_manifest = get_skills_manifest()
                run_epic_smoke_test(decision.get("epic_title", "Без названия"), fresh_manifest)
        else:
            send_tg(f"⚠️ Навык <code>{mod_name}</code> прошёл тесты, но не смёржился (HTTP {m_res.status_code}). Ветка сохранена.")
    else:
        append_failure_lesson_directly(mod_name, action, rounds_used, cheats_caught, last_error)

        issue_url = escalate_to_github_issue(mod_name, decision.get('description', ''), last_error, branch)

        err_snippet = last_error.splitlines()[-5:] if last_error else ["Неизвестная ошибка"]
        escaped_err = html.escape("\n".join(err_snippet))

        if issue_url:
            send_tg(
                f"❌ <b>Мутация застряла</b>\n━━━━━━━━━━━━━━━━━━━\n"
                f"<code>{mod_name}</code>\n"
                f"🚨 Передано Jules, ветка <code>{branch}</code> сохранена\n\n"
                f"<b>Последняя ошибка:</b>\n<pre>{escaped_err}</pre>",
                buttons=tg_issue_button(issue_url)
            )
        else:
            requests.delete(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{branch}"), headers=API_HEADERS)
            send_tg(
                f"❌ <b>Мутация отбракована</b>\n━━━━━━━━━━━━━━━━━━━\n"
                f"<code>{mod_name}</code>\n\n"
                f"<b>Ошибка:</b>\n<pre>{escaped_err}</pre>"
            )

def life_cycle():
    while True:
        try:
            run_evolution_cycle()
        except Exception as e:
            print(f"[!] Сбой цикла: {e}")
        time.sleep(900)

if __name__ == "__main__":
    threading.Thread(target=run_jules_babysitter, daemon=True).start()
    threading.Thread(target=life_cycle, daemon=True).start()
    threading.Event().wait()
