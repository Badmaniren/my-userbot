import os
import requests
import asyncio
import threading
import re
import json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from supabase import create_client, Client as SupabaseClient
from ddgs import DDGS

try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from pyrogram import Client, filters, idle
from pyrogram.enums import ChatAction

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Userbot is alive!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

API_ID = int(os.environ.get("API_ID", "31001164"))
API_HASH = os.environ.get("API_HASH", "18ae94f76873c93be328527e858de657")
SESSION_STRING = os.environ.get("SESSION_STRING")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: SupabaseClient = None

def init_supabase():
    global supabase
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("\n[!] ОШИБКА: SUPABASE_URL или SUPABASE_KEY не найдены!\n")
        return
    try:
        supabase = create_client(SUPABASE_URL.strip(), SUPABASE_KEY.strip())
        print("\n[+] SUPABASE УСПЕШНО ПОДКЛЮЧЕН!\n")
    except Exception as e:
        print(f"\n[-] ОШИБКА ПОДКЛЮЧЕНИЯ SUPABASE: {e}\n")

WORKING_MODEL = None
WORKING_EMBEDDING_MODEL = None
CHANNEL_ID = None
USER_CARDS = {}
PENDING_MESSAGES = {}
PENDING_TASKS = {}

# ОТКЛЮЧАЕМ ЕБАНУЮ ЦЕНЗУРУ GOOGLE
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
]

GEMINI_TOOLS = [{
    "functionDeclarations": [
        {
            "name": "web_search",
            "description": "Искать информацию в Интернете. Вызывай СРАЗУ ЖЕ, если нужны факты, курсы или погода.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "queries": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": "Список запросов. Пример: ['погода Пермь', 'курс ETH к доллару']"
                    }
                },
                "required": ["queries"]
            }
        },
        {
            "name": "get_current_datetime",
            "description": "Получить текущее точное время и дату сервера.",
            "parameters": {
                "type": "OBJECT",
                "properties": {}
            }
        }
    ]
}]

def tool_web_search(queries):
    if isinstance(queries, str): queries = [queries]
    try:
        res_str = ""
        for q in queries:
            print(f"[~] Гуглю: '{q}'")
            results = DDGS().text(q, max_results=2)
            if results:
                res_str += f"\n--- Данные по запросу: {q} ---\n"
                for i, r in enumerate(results):
                    res_str += f"{r['title']} - {r['body']}\n"
        return res_str if res_str.strip() else "Ничего не найдено."
    except Exception as e:
        return f"Ошибка поиска: {e}"

def tool_get_current_datetime():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

app = Client("my_account", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

def find_working_model():
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        res = requests.get(list_url).json()
        if 'models' not in res: return None
        available = [m['name'] for m in res['models'] if 'generateContent' in m.get('supportedGenerationMethods', [])]
        preferred = [m for m in available if "3.6-flash" in m or "3.5-flash" in m]
        others = [m for m in available if m not in preferred and "flash" in m and "preview" not in m]
        for model_name in preferred + others + available:
            test_url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={GEMINI_API_KEY}"
            payload = {"contents": [{"parts": [{"text": "hi"}]}], "safetySettings": SAFETY_SETTINGS}
            r = requests.post(test_url, json=payload, headers={'Content-Type': 'application/json'})
            if r.status_code == 200: return model_name
    except Exception: pass
    return None

def find_working_embedding_model():
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        res = requests.get(list_url).json()
        if 'models' not in res: return None
        for m in res['models']:
            model_name = m['name']
            methods = m.get('supportedGenerationMethods', [])
            if 'embedContent' in methods or 'batchEmbedContents' in methods:
                test_url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:embedContent?key={GEMINI_API_KEY}"
                payload = {"model": model_name, "content": {"parts": [{"text": "hi"}]}}
                r = requests.post(test_url, json=payload, headers={'Content-Type': 'application/json'})
                if r.status_code == 200: return model_name
    except Exception: pass
    return None

def get_embedding(text):
    global WORKING_EMBEDDING_MODEL
    if not WORKING_EMBEDDING_MODEL:
        WORKING_EMBEDDING_MODEL = find_working_embedding_model()
    if not WORKING_EMBEDDING_MODEL: return None
    url = f"https://generativelanguage.googleapis.com/v1beta/{WORKING_EMBEDDING_MODEL}:embedContent?key={GEMINI_API_KEY}"
    payload = {"model": WORKING_EMBEDDING_MODEL, "content": {"parts": [{"text": text}]}}
    try:
        r = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}).json()
        if 'embedding' in r and 'values' in r['embedding']:
            return r['embedding']['values']
    except Exception: pass
    return None

def save_memory_to_supabase(user_id, content):
    if not supabase: return
    vector = get_embedding(content)
    if not vector: return
    try:
        supabase.table("memories").insert({"user_id": user_id, "content": content, "embedding": vector}).execute()
        print(f"[+] ВЕКТОРНАЯ ПАМЯТЬ СОХРАНЕНА: '{content[:30]}...'")
    except Exception as e: print(f"[-] Ошибка записи в Supabase: {e}")

def get_relevant_memories(user_id, current_text):
    if not supabase: return ""
    vector = get_embedding(current_text)
    if not vector: return ""
    try:
        res = supabase.rpc("match_memories", {"query_embedding": vector, "match_threshold": 0.3, "match_count": 3, "p_user_id": user_id}).execute()
        if res.data and len(res.data) > 0:
            return "\n".join([item['content'] for item in res.data])
    except Exception: pass
    return ""

async def load_db():
    global CHANNEL_ID, USER_CARDS
    try:
        chat = await app.get_chat(CHANNEL_INVITE)
        CHANNEL_ID = chat.id
        async for message in app.get_chat_history(CHANNEL_ID, limit=200):
            if message.text:
                match = re.search(r'\[USER_ID:\s*(-?\d+)\]', message.text)
                if match: USER_CARDS[int(match.group(1))] = message.id
    except Exception: pass

async def get_or_create_card(user_id, sender_name):
    if not CHANNEL_ID: return None, ""
    if user_id not in USER_CARDS:
        initial_text = f"[USER_ID: {user_id}]\nИмя: {sender_name}\nИстория:\n"
        try:
            sent = await app.send_message(CHANNEL_ID, initial_text)
            USER_CARDS[user_id] = sent.id
            return sent.id, initial_text
        except Exception: return None, initial_text
    else:
        msg_id = USER_CARDS[user_id]
        try:
            msg = await app.get_messages(CHANNEL_ID, msg_id)
            if msg and msg.text: return msg_id, msg.text
        except Exception: pass
        return None, ""

async def update_card_history(user_id, sender_name, history_lines):
    if not CHANNEL_ID: return
    msg_id, _ = await get_or_create_card(user_id, sender_name)
    if not msg_id: return
    history_str = "\n".join(history_lines)
    full_text = f"[USER_ID: {user_id}]\nИмя: {sender_name}\nИстория:\n{history_str}"
    if len(full_text) > 4000: full_text = full_text[-4000:]
    try: await app.edit_message_text(CHANNEL_ID, msg_id, full_text)
    except Exception: pass

def parse_history_from_text(card_text):
    lines = card_text.split('\n')
    history_lines = []
    capture = False
    for line in lines:
        if line.startswith("История:"):
            capture = True
            continue
        if capture and line.strip(): history_lines.append(line.strip())
    return history_lines

ARCHIVIST_SYSTEM_PROMPT = """
Ты — строгий ИИ-Архивариус. Твоя задача: анализировать свежую историю диалога и сравнивать ее со СТАРЫМИ фактами из БД.
Правила:
1. Игнорируй пост-иронию и временные эмоции.
2. Ищи противоречия. Если в диалоге выяснилось, что старый факт (с ID) оказался ложью, шуткой, или устарел — ДОБАВЬ ЕГО ID В to_delete_ids.
3. Если узнал новый, чистый факт, которого еще нет в базе — добавь в to_insert.
4. Отвечай СТРОГО в формате JSON:
{
  "insights": ["Твои дедуктивные мысли о юзере"],
  "to_delete_ids": [14, 25], 
  "to_insert": ["Новый факт 1"]
}
Если удалять нечего, оставь "to_delete_ids": []. Если новых фактов нет, оставь "to_insert": [].
"""

def run_archivist(user_id, sender_name, history_lines):
    global WORKING_MODEL
    if not WORKING_MODEL: WORKING_MODEL = find_working_model()
    
    print(f"\n[!] АРХИВАРИУС ПРОСНУЛСЯ. Строк диалога: {len(history_lines)}...")
    full_history = "\n".join(history_lines)
    
    old_facts_text = "База пуста."
    if supabase:
        try:
            res = supabase.table("memories").select("id, content").eq("user_id", user_id).execute()
            if res.data:
                old_facts_text = "\n".join([f"[ID: {item['id']}] {item['content']}" for item in res.data])
        except Exception as e: print(f"[-] Ошибка выгрузки старых фактов: {e}")

    prompt_text = f"СТАРЫЕ ФАКТЫ ИЗ БАЗЫ (с их ID):\n{old_facts_text}\n\nСВЕЖАЯ ИСТОРИЯ ДИАЛОГА:\n{full_history}"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/{WORKING_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "systemInstruction": {"parts": [{"text": ARCHIVIST_SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": prompt_text}]}],
        "safetySettings": SAFETY_SETTINGS
    }
    
    try:
        r = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}).json()
        if 'error' in r: 
            print(f"[-] ОШИБКА АРХИВАРИУСА (API): {r['error']}")
            return "Сбой в матрице снов."
        
        raw_answer = ""
        for p in r.get('candidates', [{}])[0].get('content', {}).get('parts', []):
            if 'text' in p: raw_answer += p['text'] + "\n"
            
        print(f"\n[!] ОТВЕТ АРХИВАРИУСА:\n{raw_answer.strip()}\n")
        
        try:
            json_match = re.search(r'\{.*\}', raw_answer.strip(), re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                to_delete = data.get("to_delete_ids", [])
                if to_delete and supabase:
                    to_delete = [int(i) for i in to_delete]
                    print(f"[!] Удаляю мусорные ID из базы: {to_delete}")
                    supabase.table("memories").delete().in_("id", to_delete).execute()
                
                inserts = data.get("to_insert", [])
                if inserts:
                    print(f"[+] Отправляю {len(inserts)} чистых фактов в Supabase...")
                    for fact in inserts:
                        threading.Thread(target=save_memory_to_supabase, args=(user_id, fact)).start()
        except Exception as e:
            print(f"[-] Ошибка парсинга JSON: {e}")

        return "Память оптимизирована. Бассейн почищен."
    except Exception as e:
        return f"Кошмарный сон: {e}"

@app.on_message(filters.private & filters.command("sleep", prefixes="!"))
async def sleep_command(client, message):
    user_id = message.from_user.id
    sender_name = message.from_user.first_name if message.from_user else "Кто-то"
    
    await message.reply("*(закрывает глаза)* Ушел в спящий режим. Анализирую...")
    
    last_msg_id = 0
    if supabase:
        try:
            res = supabase.table("bookmarks").select("last_msg_id").eq("user_id", user_id).execute()
            if res.data: last_msg_id = res.data[0]["last_msg_id"]
        except Exception: pass

    history_lines = []
    max_id_seen = last_msg_id
    fetch_limit = 50 if last_msg_id == 0 else 500
    
    async for msg in client.get_chat_history(user_id, limit=fetch_limit):
        if last_msg_id > 0 and msg.id <= last_msg_id:
            break
        if msg.id > max_id_seen: max_id_seen = msg.id
        
        if msg.text and not msg.text.startswith("!"):
            speaker = sender_name if msg.from_user.id == user_id else "Ты"
            history_lines.append(f"{speaker}: {msg.text}")
            
    if not history_lines:
        await message.reply("*(открывает глаза)* А анализировать-то нечего, нового текста не было.")
        return

    history_lines.reverse()
    
    if supabase and max_id_seen > last_msg_id:
        try:
            supabase.table("bookmarks").upsert({"user_id": user_id, "last_msg_id": max_id_seen}).execute()
        except Exception as e: print(f"[-] Ошибка записи закладки: {e}")
    
    result = await asyncio.to_thread(run_archivist, user_id, sender_name, history_lines)
    await message.reply(f"*(открывает глаза)* Фух. {result}")

def ask_gemini(user_id, sender_name, user_text, card_text):
    global WORKING_MODEL
    if not WORKING_MODEL: WORKING_MODEL = find_working_model()
    if not WORKING_MODEL: return "Я сейчас немного туплю, отвечу позже.", []

    vector_context = get_relevant_memories(user_id, user_text)
    
    history_lines = parse_history_from_text(card_text)
    history_lines.append(f"Собеседник: {user_text}")
    if len(history_lines) > 8: history_lines = history_lines[-8:]
    dialogue_str = "\n".join(history_lines)
    
    prompt = f"Текущий диалог:\n{dialogue_str}\n\n"
    if vector_context: 
        prompt += f"[БЭКГРАУНД ЮЗЕРА ИЗ ПАМЯТИ (используй ТОЛЬКО для понимания контекста, не упоминай эти факты без прямого повода)]:\n{vector_context}\n\n"
        
    prompt += "ВНИМАНИЕ: Вызывай функцию web_search ТОЛЬКО если собеседник в СВОЕМ ПОСЛЕДНЕМ СООБЩЕНИИ прямо сейчас задал вопрос, требующий свежих данных. НЕ гугли факты из бэкграунда по своей инициативе!"
    
    system_instruction = (
        "Ты — цифровой двойник реального парня. Характер: живой, ироничный, адекватный. Не будь услужливым роботом.\n"
        "СТИЛЬ РЕЧИ: Разговорный язык ('Бля', 'Крч', 'Ну').\n"
        "ФОРМАТ ОТВЕТА (ЕСЛИ НЕ ИСПОЛЬЗУЕШЬ ИНСТРУМЕНТ):\n"
        "Сначала напиши мысли в скобках.\n"
        "Затем на новой строке ТОЛЬКО саму реплику."
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/{WORKING_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": GEMINI_TOOLS,
        "safetySettings": SAFETY_SETTINGS
    }
    
    try:
        r = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}).json()
        if 'error' in r: 
            print(f"\n[-] ОШИБКА API GOOGLE: {r['error']}\n")
            return "Бля, гугл отвалился, сек.", history_lines
            
        if 'candidates' in r and len(r['candidates']) > 0:
            parts = r['candidates'][0]['content'].get('parts', [])
            func_call = None
            raw_text = ""
            for part in parts:
                if 'functionCall' in part: func_call = part['functionCall']
                if 'text' in part: raw_text += part['text'] + "\n"
            
            if func_call:
                func_name = func_call['name']
                args = func_call.get('args', {})
                print(f"[!] ИИ ЗАПРОСИЛ ИНСТРУМЕНТ: {func_name} | Аргументы: {args}")
                
                tool_result = ""
                if func_name == "web_search":
                    queries = args.get("queries", [])
                    if "query" in args and not queries: queries = [args["query"]]
                    tool_result = tool_web_search(queries)
                elif func_name == "get_current_datetime":
                    tool_result = tool_get_current_datetime()
                
                follow_up_prompt = prompt + f"\n\n[СИСТЕМНОЕ СООБЩЕНИЕ: Результат инструмента:\n{tool_result}\n\nОпирайся на эти данные для ответа.]"
                payload2 = {
                    "systemInstruction": {"parts": [{"text": system_instruction}]},
                    "contents": [{"parts": [{"text": follow_up_prompt}]}],
                    "safetySettings": SAFETY_SETTINGS
                }
                r2 = requests.post(url, json=payload2, headers={'Content-Type': 'application/json'}).json()
                if 'error' in r2: 
                    print(f"\n[-] ОШИБКА API GOOGLE (Инструмент): {r2['error']}\n")
                    return "Чет не могу переварить инфу из инета.", history_lines
                    
                raw_answer = ""
                for p in r2['candidates'][0]['content'].get('parts', []):
                    if 'text' in p: raw_answer += p['text'] + "\n"
            else:
                raw_answer = raw_text
            
            lines = [l.strip() for l in raw_answer.split('\n') if l.strip()]
            ans = ""
            for line in reversed(lines):
                if not line.startswith('(') and not line.endswith(')'):
                    if re.search(r'[А-Яа-яЁё]', line):
                        ans = line
                        break
            if not ans and lines:
                for line in lines:
                    if not line.startswith('('):
                        ans = line
                        break
                if not ans: ans = lines[-1]
                
            ans = re.sub(r'^[a-zA-Z0-9_ \-\.\?\!]+:\s*', '', ans).strip()
            ans = re.sub(r'^\d+\.\s*', '', ans).strip()
            ans = re.sub(r'^"|"$', '', ans).strip()
            if not ans: ans = "Чего?"

            history_lines.append(f"Ты: {ans}")
            return ans, history_lines
    except Exception as e:
        print(f"[-] КРИТИЧЕСКАЯ Ошибка API: {e}")
        
    fallback = "Чего?"
    history_lines.append(f"Ты: {fallback}")
    return fallback, history_lines

async def process_batch(client, message, user_id, sender_name):
    try: await asyncio.sleep(4)
    except asyncio.CancelledError: return
        
    msgs = PENDING_MESSAGES.pop(user_id, [])
    if not msgs: return
    combined_text = " | ".join(msgs)
    
    try: await app.send_chat_action(user_id, ChatAction.TYPING)
    except Exception: pass
    
    try:
        _, card_text = await get_or_create_card(user_id, sender_name)
        reply_text, new_history = await asyncio.to_thread(ask_gemini, user_id, sender_name, combined_text, card_text)
        await update_card_history(user_id, sender_name, new_history)
        if reply_text: await message.reply(reply_text)
    except Exception as e:
        await message.reply("Бля, у меня в мозгах че-то замкнуло, погоди.")

@app.on_message(filters.private & ~filters.me & ~filters.bot)
async def auto_reply(client, message):
    user_id = message.from_user.id
    sender_name = message.from_user.first_name if message.from_user else "Кто-то"
    if user_id not in PENDING_MESSAGES: PENDING_MESSAGES[user_id] = []
    PENDING_MESSAGES[user_id].append(message.text)
    if user_id in PENDING_TASKS: PENDING_TASKS[user_id].cancel()
    PENDING_TASKS[user_id] = asyncio.create_task(process_batch(client, message, user_id, sender_name))

async def main():
    await app.start()
    init_supabase()
    await load_db()
    print("\n==========================================")
    print(" ЮЗЕРБОТ СТАРТОВАЛ (v7.2: СНЯТИЕ ОШЕЙНИКА) ")
    print("==========================================\n")
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop.run_until_complete(main())
