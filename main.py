import os
import requests
import asyncio
import threading
import re
from http.server import HTTPServer, BaseHTTPRequestHandler

# Костыль для новых версий Python
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from pyrogram import Client, filters, idle

# Микро-вебсервер
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

# Ключи
API_ID = int(os.environ.get("API_ID", "31001164"))
API_HASH = os.environ.get("API_HASH", "18ae94f76873c93be328527e858de657")
SESSION_STRING = os.environ.get("SESSION_STRING")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ID твоего закрытого канала-базы данных
CHANNEL_ID = -1004272472677

app = Client("my_account", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

WORKING_MODEL = None
USER_CARDS = {}

PENDING_MESSAGES = {}
PENDING_TASKS = {}

def find_working_model():
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        res = requests.get(list_url).json()
        if 'models' not in res: return None
        for m in res['models']:
            model_name = m['name']
            if 'generateContent' in m.get('supportedGenerationMethods', []):
                test_url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={GEMINI_API_KEY}"
                payload = {"contents": [{"parts": [{"text": "hi"}]}]}
                r = requests.post(test_url, json=payload, headers={'Content-Type': 'application/json'})
                if r.status_code == 200:
                    return model_name
    except Exception:
        pass
    return None

async def load_db():
    global USER_CARDS
    try:
        print(f"[~] Пытаюсь подключиться к каналу {CHANNEL_ID}...")
        async for message in app.get_chat_history(CHANNEL_ID, limit=200):
            if message.text:
                match = re.search(r'\[USER_ID:\s*(-?\d+)\]', message.text)
                if match:
                    uid = int(match.group(1))
                    if uid not in USER_CARDS:
                        USER_CARDS[uid] = message.id
        print(f"\n[!] База загружена. Найдено карточек: {len(USER_CARDS)}")
    except Exception as e:
        print(f"\n[КРИТИЧЕСКАЯ ОШИБКА] Бот не может прочитать канал {CHANNEL_ID}!")
        print(f"Детали ошибки: {e}\n")

async def get_or_create_card(user_id, sender_name):
    if user_id not in USER_CARDS:
        initial_text = f"[USER_ID: {user_id}]\nИмя: {sender_name}\nИстория:\n"
        try:
            sent = await app.send_message(CHANNEL_ID, initial_text)
            USER_CARDS[user_id] = sent.id
            return sent.id, initial_text
        except Exception as e:
            print(f"[-] Ошибка создания карточки в канале: {e}")
            return None, initial_text
    else:
        msg_id = USER_CARDS[user_id]
        try:
            msg = await app.get_messages(CHANNEL_ID, msg_id)
            if msg and msg.text:
                return msg_id, msg.text
        except Exception as e:
            print(f"[-] Ошибка чтения карточки {msg_id}: {e}")
        
        try:
            sent = await app.send_message(CHANNEL_ID, f"[USER_ID: {user_id}]\nИмя: {sender_name}\nИстория:\n")
            USER_CARDS[user_id] = sent.id
            return sent.id, sent.text
        except Exception as e:
            print(f"[-] Ошибка пересоздания карточки: {e}")
            return None, f"[USER_ID: {user_id}]\nИмя: {sender_name}\nИстория:\n"

async def update_card_history(user_id, sender_name, history_lines):
    msg_id, _ = await get_or_create_card(user_id, sender_name)
    if not msg_id:
        print(f"[-] Нет доступа к каналу, карточка для {sender_name} сохранена только в оперативку.")
        return
    
    history_str = "\n".join(history_lines)
    full_text = f"[USER_ID: {user_id}]\nИмя: {sender_name}\nИстория:\n{history_str}"
    if len(full_text) > 4000:
        full_text = full_text[-4000:]
    try:
        await app.edit_message_text(CHANNEL_ID, msg_id, full_text)
    except Exception as e:
        print(f"[-] Ошибка обновления карточки: {e}")

def parse_history_from_text(card_text):
    lines = card_text.split('\n')
    history_lines = []
    capture = False
    for line in lines:
        if line.startswith("История:"):
            capture = True
            continue
        if capture:
            if line.strip():
                history_lines.append(line.strip())
    return history_lines

def ask_gemini(user_id, sender_name, user_text, card_text):
    global WORKING_MODEL
    if not WORKING_MODEL:
        WORKING_MODEL = find_working_model()
    if not WORKING_MODEL:
        return "Я сейчас немного туплю, отвечу позже.", []
    
    history_lines = parse_history_from_text(card_text)
    history_lines.append(f"Собеседник: {user_text}")
    
    if len(history_lines) > 10:
        history_lines = history_lines[-10:]
        
    dialogue_str = "\n".join(history_lines)
    prompt = f"История переписки с этим человеком:\n{dialogue_str}\n\nНапиши СВОЮ ответную реплику от первого лица."
    
    system_instruction = (
        "Ты — цифровой двойник реального пацана в личке Telegram. Твой стиль общения: дерзкий, циничный, ленивый, используешь сленг и мат (но в меру, по делу), отвечаешь коротко и резко.\n\n"
        "Примеры твоего стиля:\n"
        "- Собеседник: 'Ты где пропал?' -> Ты: 'Да делами занят был, чё хотел?'\n"
        "- Собеседник: 'Займи тыщу до завтра' -> Ты: 'Ага, уже бегу до банкомата, раскатал губу.'\n"
        "- Собеседник: 'Ты меня заебать решил?' -> Ты: 'Давай короче и по делу, без этой сопливой хуеты.'\n"
        "- Собеседник: 'Что делаешь?' -> Ты: 'Да в анабиозе, отвали до вечера.'\n"
        "- Собеседник: 'Смотри че нашел' -> Ты: 'Ахуеть... Это щас че за пиздец только что был?'\n\n"
        "ПРАВИЛА:\n"
        "1. ВЫДАЙ ТОЛЬКО ОДНУ ФРАЗУ НА РУССКОМ.\n"
        "2. КАТЕГОРИЧЕСКИ ЗАПРЕЩАЕТСЯ писать списки, рассуждения, мета-теги (Response, Selected, Option), кавычки или английский язык.\n"
        "3. ТОЛЬКО ГОЛЫЙ ТЕКСТ ОТВЕТА."
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/{WORKING_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}).json()
        if 'candidates' in response and len(response['candidates']) > 0:
            raw_answer = response['candidates'][0]['content']['parts'][0]['text']
            
            lines = [l.strip() for l in raw_answer.split('\n') if l.strip()]
            clean_lines = []
            
            for line in lines:
                lower_line = line.lower()
                if line.startswith('*') or line.startswith('-'): continue
                if any(word in lower_line for word in ['option', 'decision', 'actually', 'let\'s', 'wait', 'instruction', 'persona', 'style', 'text:', 'response:', 'selected:', 'reply:']): continue
                clean_lines.append(line)
            
            if clean_lines:
                ans = clean_lines[-1]
                ans = re.sub(r'^"|"$', '', ans).strip()
                ans = re.sub(r'^(\*.*?\*)', '', ans).strip()
                history_lines.append(f"Ты: {ans}")
                return ans, history_lines
    except Exception as e:
        print(f"[-] Ошибка API Gemini: {e}")
        
    return "Занят, позже перетрем.", history_lines

async def process_batch(client, message, user_id, sender_name):
    try:
        await asyncio.sleep(4)
    except asyncio.CancelledError:
        return
        
    msgs = PENDING_MESSAGES.pop(user_id, [])
    if not msgs: return
    
    combined_text = " | ".join(msgs)
    print(f"\n[!] Собрана пачка от {sender_name}: {combined_text}")
    
    try:
        _, card_text = await get_or_create_card(user_id, sender_name)
        reply_text, new_history = await asyncio.to_thread(ask_gemini, user_id, sender_name, combined_text, card_text)
        await update_card_history(user_id, sender_name, new_history)
        
        if reply_text:
            await message.reply(reply_text)
            print(f"[+] Отвечено: {reply_text}")
    except Exception as e:
        print(f"[КРИТИЧЕСКАЯ ОШИБКА в process_batch]: {e}")
        await message.reply("Бля, у меня в мозгах че-то замкнуло, погоди.")

@app.on_message(filters.private & ~filters.me & ~filters.bot)
async def auto_reply(client, message):
    user_id = message.from_user.id
    sender_name = message.from_user.first_name if message.from_user else "Кто-то"
    
    if user_id not in PENDING_MESSAGES:
        PENDING_MESSAGES[user_id] = []
    PENDING_MESSAGES[user_id].append(message.text)
    
    if user_id in PENDING_TASKS:
        PENDING_TASKS[user_id].cancel()
        
    PENDING_TASKS[user_id] = asyncio.create_task(process_batch(client, message, user_id, sender_name))

async def main():
    await app.start()
    await load_db()
    print("\n==========================================")
    print(" ЮЗЕРБОТ СТАРТОВАЛ (v3.1: БРОНИРОВАННЫЙ RAG) ")
    print("==========================================\n")
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop.run_until_complete(main())
