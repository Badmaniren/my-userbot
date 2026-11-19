import os
import gc
import sys
import time
import uuid
import base64
import re
import json
import ssl
import socket
import struct
import hashlib
import random
import html
import urllib.parse
import requests
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from collections import deque

# =====================================================================
# 1. ИНИЦИАЛИЗАЦИЯ И КРИПТО-КЛЮЧЕЙ СЕРВЕРА
# =====================================================================
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.environ.get("GITHUB_REPO", "").strip()
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TG_ADMIN_ID = os.environ.get("TELEGRAM_ADMIN_ID", "").strip()

RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "").strip().rstrip("/")
RENDER_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
if not RENDER_HOSTNAME and RENDER_EXTERNAL_URL:
    RENDER_HOSTNAME = urllib.parse.urlsplit(RENDER_EXTERNAL_URL).hostname or ""

_SEED = f"{GITHUB_TOKEN}:{GITHUB_REPO}:{TG_TOKEN}:hijacker_v1"
SUB_TOKEN = os.environ.get("SUB_TOKEN", hashlib.sha256(_SEED.encode()).hexdigest()[:16])
WS_SECRET_PATH = f"/ws-{SUB_TOKEN}"
VLESS_UUID = str(uuid.UUID(bytes=hashlib.md5(_SEED.encode()).digest()))
VLESS_UUID_BYTES = uuid.UUID(VLESS_UUID).bytes

VPN_LOCK = threading.Lock()
STATE_LOCK = threading.Lock()
VPN_REFRESH_EVENT = threading.Event()
HARVEST_RUNNING = False

GH_SESSION = requests.Session()
if GITHUB_TOKEN:
    GH_SESSION.headers.update({
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.text-match+json",
        "User-Agent": "Premium-Hijacker/1.0"
    })

TG_SESSION = requests.Session()
HTTP_SCRAPER = requests.Session()
HTTP_SCRAPER.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0.0.0 Safari/537.36"
})

GITHUB_BASE = "https://api.github.com/repos/"

VPN_STATE = {
    "last_updated": "Ожидание охоты...",
    "verified_nodes": [],
    "raw_uris": [],
    "sub_base64": "",
    "singbox_json": "",
    "custom_sni": ["st.ozone.ru", "stats.vk-portal.net", "sba.yandex.net"],
    "clean_cf_ips": ["104.16.132.229", "188.114.96.1"],
    "relay_connections": 0,
    "relay_bytes": 0,
    "hijacked_count": 0
}

# =====================================================================
# 2. РЕЗЕРВНЫЙ VLESS НА RENDER (НЕ ТРОГАЕМ, РАБОТАЕТ ИДЕАЛЬНО)
# =====================================================================
def get_self_vless_uri(custom_host: str = "") -> str:
    host = custom_host or RENDER_HOSTNAME or "my-userbot-3j04.onrender.com"
    params = urllib.parse.urlencode({
        "encryption": "none",
        "security": "tls",
        "sni": host,
        "fp": "chrome",
        "type": "ws",
        "host": host,
        "path": WS_SECRET_PATH,
        "alpn": "http/1.1"
    })
    return f"vless://{VLESS_UUID}@{host}:443?{params}#{urllib.parse.quote('👑 РЕЗЕРВ RENDER')}"

def _ws_unmask(payload: bytes, mask_key: bytes) -> bytes:
    n = len(payload)
    if n == 0: return b""
    repeated = (mask_key * ((n // 4) + 1))[:n]
    return (int.from_bytes(payload, "big") ^ int.from_bytes(repeated, "big")).to_bytes(n, "big")

def _ws_build_frame(data: bytes, opcode: int = 0x02) -> bytes:
    n = len(data)
    header = bytearray([0x80 | opcode])
    if n < 126:
        header.append(n)
    elif n < 65536:
        header.append(126)
        header.extend(struct.pack("!H", n))
    else:
        header.append(127)
        header.extend(struct.pack("!Q", n))
    return bytes(header) + data

def _recv_exact_sock(sock: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk: raise EOFError()
        buf.extend(chunk)
    return bytes(buf)

def _ws_read_frame_sock(sock: socket.socket) -> tuple:
    b1, b2 = _recv_exact_sock(sock, 2)
    opcode = b1 & 0x0F
    masked = (b2 & 0x80) != 0
    length = b2 & 0x7F
    if length == 126:
        length = struct.unpack("!H", _recv_exact_sock(sock, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", _recv_exact_sock(sock, 8))[0]
    mask_key = _recv_exact_sock(sock, 4) if masked else b""
    payload = _recv_exact_sock(sock, length)
    if masked: payload = _ws_unmask(payload, mask_key)
    return opcode, payload

def handle_vless_websocket_tunnel(handler: BaseHTTPRequestHandler):
    ws_key = handler.headers.get("Sec-WebSocket-Key", "").strip()
    if not ws_key: return
    accept_val = base64.b64encode(hashlib.sha1((ws_key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()).decode("ascii")
    client_sock = handler.connection
    client_sock.settimeout(30)
    try: client_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except: pass
    client_sock.sendall(("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: " + accept_val + "\r\n\r\n").encode("ascii"))
    write_lock = threading.Lock()
    target_sock = None
    stop_event = threading.Event()

    def _ws_send(data: bytes, opcode: int = 0x02):
        with write_lock: client_sock.sendall(_ws_build_frame(data, opcode=opcode))

    try:
        first_payload = b""
        while not first_payload:
            op, pl = _ws_read_frame_sock(client_sock)
            if op == 0x08: return
            if op == 0x09: _ws_send(pl, opcode=0x0A); continue
            if op in (0x01, 0x02, 0x00) and pl: first_payload = pl
        
        if len(first_payload) < 24 or first_payload[0] != 0 or first_payload[1:17] != VLESS_UUID_BYTES: return
        addons_len = first_payload[17]
        pos = 18 + addons_len
        if first_payload[pos] != 1: return
        dst_port = struct.unpack("!H", first_payload[pos + 1:pos + 3])[0]
        atyp = first_payload[pos + 3]
        pos += 4
        if atyp == 1: dst_host, pos = socket.inet_ntoa(first_payload[pos:pos + 4]), pos + 4
        elif atyp == 2: dst_host, pos = first_payload[pos + 1:pos + 1 + first_payload[pos]].decode(), pos + 1 + first_payload[pos]
        elif atyp == 3: dst_host, pos = socket.inet_ntop(socket.AF_INET6, first_payload[pos:pos + 16]), pos + 16
        else: return

        initial_tcp_data = first_payload[pos:]
        target_sock = socket.create_connection((dst_host, dst_port), timeout=10)
        target_sock.settimeout(30)
        
        with VPN_LOCK: VPN_STATE["relay_connections"] += 1
        if initial_tcp_data:
            target_sock.sendall(initial_tcp_data)
            with VPN_LOCK: VPN_STATE["relay_bytes"] += len(initial_tcp_data)

        def _pump_target_to_ws():
            first = True
            try:
                while not stop_event.is_set():
                    data = target_sock.recv(16384)
                    if not data: break
                    if first: data = b"\x00\x00" + data; first = False
                    _ws_send(data, opcode=0x02)
                    with VPN_LOCK: VPN_STATE["relay_bytes"] += len(data)
            except: pass
            finally: stop_event.set()

        threading.Thread(target=_pump_target_to_ws, daemon=True).start()
        while not stop_event.is_set():
            op, pl = _ws_read_frame_sock(client_sock)
            if op == 0x08: break
            elif op == 0x09: _ws_send(pl, opcode=0x0A)
            elif op in (0x01, 0x02, 0x00) and pl:
                target_sock.sendall(pl)
                with VPN_LOCK: VPN_STATE["relay_bytes"] += len(pl)
    except: pass
    finally:
        stop_event.set()
        if target_sock:
            try: target_sock.close()
            except: pass


# =====================================================================
# 3. STEALTH HUNTER: ПАРСИНГ УТЕЧЕК ЧЕРЕЗ GITHUB API
# =====================================================================
_SHARED_SSL_CTX = ssl.create_default_context()
_SHARED_SSL_CTX.check_hostname = False
_SHARED_SSL_CTX.verify_mode = ssl.CERT_NONE

def _build_tls13_client_hello(sni: str) -> bytes:
    sni_bytes = sni.encode("idna")
    sni_ext = struct.pack("!HHBH", 0x0000, len(sni_bytes) + 5, 0x00, len(sni_bytes)) + sni_bytes
    exts = sni_ext + b"\x00\x2b\x00\x03\x02\x03\x04"
    body = b"\x03\x03" + os.urandom(32) + b"\x00" + b"\x00\x04\x13\x01\x13\x02" + b"\x01\x00" + struct.pack("!H", len(exts)) + exts
    hs = b"\x01" + len(body).to_bytes(3, "big") + body
    return b"\x16\x03\x01" + struct.pack("!H", len(hs)) + hs

def extract_uris_from_text(text: str) -> list:
    """Ищет vless://, trojan:// и hy2:// в любом сыром тексте."""
    pattern = r"(vless|trojan|hysteria2|hy2)://[a-zA-Z0-9\-_\.\@\:\?\=\&\%]+"
    matches = re.findall(pattern, text)
    uris = []
    # re.findall с группами возвращает только группу, если не использовать полные совпадения, чиним это:
    for m in re.finditer(pattern, text):
        uris.append(m.group(0))
    return uris

def hunt_github_leaks() -> list:
    """Шпионит через GitHub API за свежими коммитами и гистами с приватными ключами."""
    if not GITHUB_TOKEN:
        print("[!] Нет GITHUB_TOKEN, охота через API отменяется.")
        return []
        
    found_uris = set()
    # Запросы заточены под свежие утечки панелей (VLESS Reality и Trojan)
    queries = [
        '"vless://" "pbk=" "sni="',
        '"trojan://" "sni="',
        '"hy2://" "sni="'
    ]
    
    for q in queries:
        try:
            # Ищем свежак, залитый за последние пару дней
            url = f"https://api.github.com/search/code?q={urllib.parse.quote(q)}&sort=indexed&order=desc"
            r = GH_SESSION.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                for item in data.get("items", [])[:15]:  # Берем топ-15 свежих файлов
                    # Достаем сырой текст файла
                    raw_url = item.get("html_url", "").replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                    if raw_url:
                        f_res = HTTP_SCRAPER.get(raw_url, timeout=5)
                        if f_res.status_code == 200:
                            for uri in extract_uris_from_text(f_res.text):
                                found_uris.add(uri)
            time.sleep(2)  # Чтобы не словить rate limit
        except Exception as e:
            print(f"[!] Ошибка поиска утечек '{q}': {e}")
            
    return list(found_uris)

def hunt_telegram_premium_leaks() -> list:
    """Парсит веб-превью Telegram-каналов, специализирующихся на сливах платных конфигов."""
    channels = [
        "v2ray_vpn_config", "Shadowsocks_V2ray", "FreeVless_Config", 
        "V2rayConfigsFree", "vpn_leaks_premium"
    ]
    found_uris = set()
    for ch in channels:
        try:
            r = HTTP_SCRAPER.get(f"https://t.me/s/{ch}", timeout=6)
            if r.status_code == 200:
                for uri in extract_uris_from_text(r.text):
                    found_uris.add(uri)
        except:
            pass
    return list(found_uris)

def parse_proxy_uri(uri: str) -> dict:
    try:
        parsed = urllib.parse.urlsplit(uri)
        scheme = parsed.scheme.lower()
        if scheme not in ("vless", "trojan", "hysteria2", "hy2") or "@" not in parsed.netloc:
            return {}
        userinfo, hostport = parsed.netloc.rsplit("@", 1)
        userinfo = urllib.parse.unquote(userinfo)
        if ":" in hostport:
            host, port_str = hostport.rsplit(":", 1)
            port = int(port_str)
        else:
            host, port = hostport, 443

        qs = dict(urllib.parse.parse_qsl(parsed.query))
        security = qs.get("security", "tls" if scheme in ("trojan", "hysteria2", "hy2") else "none").lower()
        net_type = qs.get("type", "tcp").lower()
        sni = qs.get("sni") or qs.get("peer") or qs.get("host") or host

        # Отсекаем мусор, берем только криптостойкие
        if scheme == "vless" and security not in ("reality", "tls"): return {}
        if security == "reality" and not qs.get("pbk"): return {}

        return {
            "scheme": "hysteria2" if scheme == "hy2" else scheme,
            "uuid_or_pass": userinfo,
            "host": host,
            "port": port,
            "params": qs,
            "security": security,
            "type": net_type,
            "sni": sni
        }
    except:
        return {}

def hijack_and_mutate_node(node: dict, whitelist_snis: list) -> dict:
    """Жёсткая проверка: оставляем ТОЛЬКО премиум (пинг < 180 мс)."""
    host = node["host"]
    port = node["port"]
    sni = node["sni"]
    security = node["security"]
    params = dict(node["params"])

    t0 = time.time()
    try:
        if node["scheme"] == "hysteria2":
            ip_addr = socket.gethostbyname(host)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as usock:
                usock.settimeout(1.0) # Жёсткий таймаут для отсева медленных
                usock.sendto(os.urandom(64), (ip_addr, port))
            latency_ms = int((time.time() - t0) * 1000) + 15
        elif security == "reality":
            with socket.create_connection((host, port), timeout=1.2) as sock:
                sock.settimeout(1.2)
                sock.sendall(_build_tls13_client_hello(sni or random.choice(whitelist_snis)))
                resp = sock.recv(5)
                if len(resp) < 3 or resp[0] != 0x16: return {}
            latency_ms = int((time.time() - t0) * 1000)
        else:
            with socket.create_connection((host, port), timeout=1.2) as sock:
                with _SHARED_SSL_CTX.wrap_socket(sock, server_hostname=sni or host):
                    pass
            latency_ms = int((time.time() - t0) * 1000)
    except:
        return {}

    # Главное отличие от паблика: премиум ноды быстрые. Режем всё, что выше 180 мс.
    if latency_ms > 180:
        return {}

    params["fp"] = "chrome"
    if security == "reality" and not params.get("sni"):
        params["sni"] = random.choice(whitelist_snis)
    elif security == "tls":
        params["alpn"] = "h2,http/1.1"

    proto_badge = "PREMIUM-REALITY" if security == "reality" else f"PREMIUM-{node['scheme'].upper()}"
    tag = f"🏴‍☠️ [{proto_badge}] {host[:15]}:{port} ({latency_ms}ms)"

    query_str = urllib.parse.urlencode(params, safe=":,/")
    mutated_uri = f"{node['scheme']}://{urllib.parse.quote(node['uuid_or_pass'])}@{host}:{port}?{query_str}#{urllib.parse.quote(tag)}"

    node_out = dict(node)
    node_out.update({
        "latency_ms": latency_ms,
        "tag": tag,
        "mutated_uri": mutated_uri
    })
    return node_out


def build_singbox_profile(nodes: list) -> dict:
    outbounds = []
    outbound_tags = []

    if RENDER_HOSTNAME:
        self_tag = f"👑 МОЙ RENDER VLESS ({RENDER_HOSTNAME})"
        outbounds.append({
            "type": "vless", "tag": self_tag, "server": RENDER_HOSTNAME, "server_port": 443,
            "uuid": VLESS_UUID,
            "tls": {"enabled": True, "server_name": RENDER_HOSTNAME, "utls": {"enabled": True, "fingerprint": "chrome"}},
            "transport": {"type": "ws", "path": WS_SECRET_PATH, "headers": {"Host": RENDER_HOSTNAME}}
        })
        outbound_tags.append(self_tag)

    for idx, n in enumerate(nodes[:20]):
        tag = f"{n['tag']} #{idx + 1}"
        p, scheme = n["params"], n["scheme"]
        
        ob = {
            "type": "vless" if scheme == "vless" else "trojan",
            "tag": tag, "server": n["host"], "server_port": n["port"],
            "tls": {"enabled": True, "server_name": p.get("sni", n["sni"]), "insecure": True, "utls": {"enabled": True, "fingerprint": "chrome"}}
        }
        if scheme == "vless":
            ob["uuid"] = n["uuid_or_pass"]
            if p.get("flow"): ob["flow"] = p["flow"]
            if n["security"] == "reality": ob["tls"]["reality"] = {"enabled": True, "public_key": p.get("pbk", ""), "short_id": p.get("sid", "")}
        else:
            ob["password"] = n["uuid_or_pass"]
            
        if n.get("type") == "ws": ob["transport"] = {"type": "ws", "path": p.get("path", "/"), "headers": {"Host": p.get("host", p.get("sni", n["host"]))}}
        outbounds.append(ob)
        outbound_tags.append(tag)

    header = [
        {"type": "selector", "tag": "🚀 ПИРАТСКИЙ ВПН", "outbounds": ["⚡ АВТО-ПИНГ"] + outbound_tags + ["direct"], "default": "⚡ АВТО-ПИНГ"},
        {"type": "urltest", "tag": "⚡ АВТО-ПИНГ", "outbounds": outbound_tags, "url": "https://www.gstatic.com/generate_204", "interval": "1m", "tolerance": 50}
    ]
    tail = [{"type": "direct", "tag": "direct"}, {"type": "block", "tag": "block"}, {"type": "dns", "tag": "dns-out"}]

    return {
        "log": {"level": "warn", "timestamp": True},
        "dns": {
            "servers": [{"tag": "dns-remote", "address": "https://1.1.1.1/dns-query", "detour": "🚀 ПИРАТСКИЙ ВПН"}, {"tag": "dns-direct", "address": "77.88.8.8", "detour": "direct"}],
            "rules": [{"domain_suffix": [".ru", ".su", ".xn--p1ai"], "server": "dns-direct"}], "final": "dns-remote"
        },
        "inbounds": [{"type": "tun", "tag": "tun-in", "inet4_address": "172.19.0.1/30", "mtu": 1400, "auto_route": True, "strict_route": True}],
        "outbounds": header + outbounds + tail,
        "route": {
            "auto_detect_interface": True,
            "rules": [{"protocol": "dns", "outbound": "dns-out"}, {"ip_is_private": True, "outbound": "direct"}, {"domain_suffix": [".ru", ".xn--p1ai", "yandex.net", "vk.com", "tbank.ru"], "outbound": "direct"}],
            "final": "🚀 ПИРАТСКИЙ ВПН"
        }
    }


def push_vpn_backup_to_github(files_dict: dict):
    if not GITHUB_TOKEN or not GITHUB_REPO: return
    try:
        ref_url = f"{GITHUB_BASE}{GITHUB_REPO}/git/ref/heads/main"
        head_sha = GH_SESSION.get(ref_url).json()["object"]["sha"]
        base_tree = GH_SESSION.get(f"{GITHUB_BASE}{GITHUB_REPO}/git/commits/{head_sha}").json()["tree"]["sha"]
        tree_items = [{"path": p, "mode": "100644", "type": "blob", "content": c} for p, c in files_dict.items()]
        new_tree = GH_SESSION.post(f"{GITHUB_BASE}{GITHUB_REPO}/git/trees", json={"base_tree": base_tree, "tree": tree_items}).json()["sha"]
        new_commit = GH_SESSION.post(f"{GITHUB_BASE}{GITHUB_REPO}/git/commits", json={"message": "🏴‍☠️ Охота завершена: заливка угнанных конфигов [skip ci]", "tree": new_tree, "parents": [head_sha]}).json()["sha"]
        GH_SESSION.patch(ref_url, json={"sha": new_commit})
    except: pass


def execute_hijack_run(notify_tg: bool = False):
    global HARVEST_RUNNING
    with STATE_LOCK:
        if HARVEST_RUNNING: return
        HARVEST_RUNNING = True

    try:
        print("[~] Начинаем охоту за утечками...")
        with VPN_LOCK: snis = list(VPN_STATE["custom_sni"])

        # Собираем сырые данные
        gh_leaks = hunt_github_leaks()
        tg_leaks = hunt_telegram_premium_leaks()
        raw_candidates = list(set(gh_leaks + tg_leaks))
        
        parsed_map = {}
        for uri in raw_candidates:
            p = parse_proxy_uri(uri)
            if p: parsed_map[f"{p['host']}:{p['port']}"] = p

        # Валидируем с жестким таймаутом (оставляем только премиум)
        verified = []
        with ThreadPoolExecutor(max_workers=20) as pool:
            for res in pool.map(lambda node: hijack_and_mutate_node(node, snis), parsed_map.values()):
                if res: verified.append(res)

        verified.sort(key=lambda x: x["latency_ms"])
        top_nodes = verified[:20]

        uris = []
        if RENDER_HOSTNAME: uris.append(get_self_vless_uri(RENDER_HOSTNAME))
        uris.extend(n["mutated_uri"] for n in top_nodes)

        sub_b64 = base64.b64encode("\n".join(uris).encode("utf-8")).decode("ascii")
        sb_json = json.dumps(build_singbox_profile(top_nodes), indent=2, ensure_ascii=False)
        now_str = datetime.now(timezone.utc).strftime("%H:%M UTC")

        with VPN_LOCK:
            VPN_STATE["last_updated"] = now_str
            VPN_STATE["verified_nodes"] = top_nodes
            VPN_STATE["raw_uris"] = uris
            VPN_STATE["sub_base64"] = sub_b64
            VPN_STATE["singbox_json"] = sb_json
            VPN_STATE["hijacked_count"] = len(top_nodes)

        push_vpn_backup_to_github({
            "vpn/sub_base64.txt": sub_b64, 
            "vpn/sub_raw.txt": "\n".join(uris), 
            "vpn/singbox_hijacked.json": sb_json
        })

        if notify_tg:
            best = top_nodes[0]['latency_ms'] if top_nodes else "N/A"
            send_tg(
                f"🏴‍☠️ <b>Охота завершена!</b>\n━━━━━━━━━━━━━━━━━━━\n"
                f"🔎 <b>Найдено зацепок:</b> {len(raw_candidates)}\n"
                f"💎 <b>Угнано премиум-нод (<180ms):</b> {len(top_nodes)}\n"
                f"⚡ <b>Лучший пинг:</b> {best} ms\n\n"
                f"Ссылки готовы, жми <code>/vpn</code>"
            )
    finally:
        with STATE_LOCK: HARVEST_RUNNING = False
        gc.collect()

def run_hunter_daemon():
    time.sleep(5)
    while True:
        try: execute_hijack_run()
        except: pass
        VPN_REFRESH_EVENT.wait(timeout=3600) # Охотимся раз в час, чаще на Github ловится бан
        VPN_REFRESH_EVENT.clear()


# =====================================================================
# 4. HTTP СЕРВЕР (САМ ТУННЕЛЬ И РАЗДАЧА ПОДПИСОК)
# =====================================================================
class GreatVPNHTTPHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    rbufsize = 0  

    def log_message(self, format, *args): pass

    def _send_text(self, code: int, body: str, content_type: str = "text/plain; charset=utf-8", extra_headers: dict = None):
        encoded = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        if extra_headers:
            for k, v in extra_headers.items(): self.send_header(k, v)
        self.end_headers()
        self.wfile.write(encoded)
        self.wfile.flush()

    def do_GET(self):
        global RENDER_HOSTNAME
        host_hdr = self.headers.get("Host", "").split(":")[0].strip()
        if host_hdr and not RENDER_HOSTNAME and "onrender.com" in host_hdr: RENDER_HOSTNAME = host_hdr
        parsed = urllib.parse.urlsplit(self.path)
        
        if parsed.path == WS_SECRET_PATH:
            handle_vless_websocket_tunnel(self)
            self.close_connection = True
            return

        qs = dict(urllib.parse.parse_qsl(parsed.query))
        if parsed.path in ("/", "/health", "/ping"):
            self._send_text(200, "Hijacker Operational")
            return

        if parsed.path in ("/sub", "/raw", "/singbox"):
            if qs.get("token", "") != SUB_TOKEN:
                self._send_text(403, "Forbidden")
                return

            with VPN_LOCK:
                sub_b64 = VPN_STATE["sub_base64"]
                raw_uris = "\n".join(VPN_STATE["raw_uris"])
                sb_json = VPN_STATE["singbox_json"]

            sub_headers = {"Profile-Title": base64.b64encode("🏴‍☠️ Premium Hijacked".encode()).decode()}
            if parsed.path == "/sub":
                self._send_text(200, sub_b64 or base64.b64encode(get_self_vless_uri(RENDER_HOSTNAME).encode()).decode(), extra_headers=sub_headers)
            elif parsed.path == "/raw":
                self._send_text(200, raw_uris or get_self_vless_uri(), extra_headers=sub_headers)
            elif parsed.path == "/singbox":
                self._send_text(200, sb_json or "{}", content_type="application/json; charset=utf-8", extra_headers=sub_headers)
            return
        self._send_text(404, "Not Found")

class PooledThreadingHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

def run_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = PooledThreadingHTTPServer(('0.0.0.0', port), GreatVPNHTTPHandler)
    server.serve_forever()

threading.Thread(target=run_http_server, daemon=True).start()
threading.Thread(target=run_hunter_daemon, daemon=True).start()


# =====================================================================
# 5. TELEGRAM ИНТЕРФЕЙС
# =====================================================================
def send_tg(text: str, buttons: list = None, keyboard: bool = False):
    if not TG_TOKEN or not TG_ADMIN_ID: return
    payload = {"chat_id": TG_ADMIN_ID, "text": text[:4000], "parse_mode": "HTML", "disable_web_page_preview": True}
    if keyboard:
        payload["reply_markup"] = json.dumps({"keyboard": [["🛡️ /vpn", "👑 /myvless"], ["🏴‍☠️ /hunt", "📊 /ping"]], "resize_keyboard": True})
    elif buttons:
        payload["reply_markup"] = json.dumps({"inline_keyboard": buttons})
    try: TG_SESSION.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", json=payload, timeout=5)
    except: pass

def set_tg_commands():
    if not TG_TOKEN: return
    commands = [
        {"command": "vpn", "description": "🛡️ Панель управления и ссылки"},
        {"command": "myvless", "description": "👑 Личный VLESS на Render"},
        {"command": "hunt", "description": "🏴‍☠️ Запустить парсинг утечек GitHub"},
        {"command": "ping", "description": "📊 Статус сессий и перехватов"},
    ]
    try: TG_SESSION.post(f"https://api.telegram.org/bot{TG_TOKEN}/setMyCommands", json={"commands": commands}, timeout=5)
    except: pass

def send_vpn_dashboard():
    with VPN_LOCK:
        nodes = list(VPN_STATE["verified_nodes"])
        upd = VPN_STATE["last_updated"]
        hijacked = VPN_STATE["hijacked_count"]
    
    base_url = f"https://{RENDER_HOSTNAME or 'my-userbot-3j04.onrender.com'}"
    sub_url = f"{base_url}/sub?token={SUB_TOKEN}"
    sb_url = f"{base_url}/singbox?token={SUB_TOKEN}"
    
    top_preview = "\n".join(f"• <code>{html.escape(n['tag'])}</code>" for n in nodes[:5]) or "<i>Пусто, жми /hunt</i>"
    
    text = (
        f"🏴‍☠️ <b>Stealth Hunter — Панель управления</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🕒 <b>Скан утечек:</b> {html.escape(upd)}\n"
        f"💎 <b>Угнано премиум-нод:</b> {hijacked}\n\n"
        f"🏆 <b>Топ-5 трофеев:</b>\n{top_preview}\n\n"
        f"🔗 <b>Подписка (Happ, v2rayNG, V2Box):</b>\n<code>{html.escape(sub_url)}</code>\n\n"
        f"📦 <b>Профиль Sing-box (с роутингом .ru):</b>\n<code>{html.escape(sb_url)}</code>"
    )
    buttons = [[{"text": "🏴‍☠️ Начать охоту", "callback_data": "start_hunt"}]]
    send_tg(text, buttons=buttons)

def run_telegram_listener():
    if not TG_TOKEN: return
    offset = 0
    set_tg_commands()
    send_tg("🏴‍☠️ <b>Stealth Hunter запущен!</b>\nЖми <code>/hunt</code>, чтобы просканировать GitHub на утечки ключей.", keyboard=True)

    while True:
        try:
            r = TG_SESSION.get(f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates", params={"offset": offset, "timeout": 20}, timeout=25)
            if r.status_code == 200:
                for update in r.json().get("result", []):
                    offset = update["update_id"] + 1
                    
                    cb = update.get("callback_query")
                    if cb:
                        if str(cb.get("message", {}).get("chat", {}).get("id", "")) != TG_ADMIN_ID: continue
                        if cb["data"] == "start_hunt":
                            send_tg("🏴‍☠️ <b>Выдвигаемся. Парсю свежие коммиты и Telegram-базы...</b>")
                            threading.Thread(target=execute_hijack_run, args=(True,), daemon=True).start()
                        continue
                        
                    msg = update.get("message", {})
                    if str(msg.get("chat", {}).get("id", "")) != TG_ADMIN_ID: continue
                    text = re.sub(r'^[🛡️👑🏴‍☠️📊]\s*', '', msg.get("text", "").strip())
                    
                    if text.startswith("/start"): send_tg("Жми /vpn или /hunt", keyboard=True)
                    elif text.startswith("/vpn"): send_vpn_dashboard()
                    elif text.startswith("/myvless"): send_tg(f"👑 <b>Твой личный резерв:</b>\n<code>{html.escape(get_self_vless_uri())}</code>")
                    elif text.startswith("/hunt"):
                        send_tg("🏴‍☠️ <b>Шпионю за GitHub и Telegram...</b>")
                        threading.Thread(target=execute_hijack_run, args=(True,), daemon=True).start()
                    elif text.startswith("/ping"):
                        with VPN_LOCK:
                            conns = VPN_STATE["relay_connections"]
                            mb = round(VPN_STATE["relay_bytes"] / (1024 * 1024), 2)
                        send_tg(f"📊 <b>Статус:</b>\nТуннель сессий: {conns}\nПрокачано: {mb} МБ\nУгнано нод: {VPN_STATE['hijacked_count']}")
        except: time.sleep(5)
        time.sleep(1)

if __name__ == "__main__":
    run_telegram_listener()
