import os
import re
import json
import time
import logging
from pathlib import Path
import urllib.request
import urllib.parse
import html
import schedule

# ----------------------------------------------------------------------
# CONFIGURACIÓN TELEGRAM
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).parent

TELEGRAM_BOT_TOKEN = "8958926765:AAHka_dr0e4kewtgyY-D0pgilYLx85wXO4w"
TELEGRAM_CHAT_ID = "708457190"

# Fuentes de ofertas (Mastodon Gamedev community + Remotive + RemoteOK)
SOURCES = [
    {
        "type": "mastodon",
        "name": "Mastodon GameDev Jobs",
        "url": "https://mastodon.gamedev.place/api/v1/timelines/tag/gamedevjobs"
    },
    {
        "type": "mastodon",
        "name": "Mastodon Game Jobs",
        "url": "https://mastodon.gamedev.place/api/v1/timelines/tag/gamejobs"
    },
    {
        "type": "mastodon",
        "name": "Mastodon 3D Artist",
        "url": "https://mastodon.gamedev.place/api/v1/timelines/tag/3dartist"
    },
    {
        "type": "remotive",
        "name": "Remotive Design & 3D",
        "url": "https://remotive.com/api/remote-jobs?category=design"
    },
    {
        "type": "remoteok",
        "name": "RemoteOK 3D & Gaming",
        "url": "https://remoteok.com/api"
    }
]

# Palabras clave de 3D / Game Art
KEYWORDS_3D = [
    r"\b3d\b",
    r"modelador",
    r"modeler",
    r"modeller",
    r"prop",
    r"props",
    r"environment",
    r"entorno",
    r"escenari",
    r"miniatur",
    r"sculpt",
    r"esculpid",
    r"blender",
    r"zbrush",
    r"asset",
    r"assets",
    r"character artist",
    r"concept art",
    r"unity",
    r"unreal"
]

# Palabras clave de contratación
KEYWORDS_HIRING = [
    r"hiring",
    r"looking for",
    r"we need",
    r"job",
    r"position",
    r"freelance",
    r"contract",
    r"remote",
    r"paid",
    r"buscamos",
    r"se busca",
    r"necesit"
]

REGEX_3D = [re.compile(k, re.IGNORECASE) for k in KEYWORDS_3D]
REGEX_HIRING = [re.compile(k, re.IGNORECASE) for k in KEYWORDS_HIRING]

HIST_FILE = BASE_DIR / "job_history.json"
if HIST_FILE.exists():
    try:
        with open(HIST_FILE, "r", encoding="utf-8") as f:
            SEEN_IDS = set(json.load(f))
    except Exception:
        SEEN_IDS = set()
else:
    SEEN_IDS = set()

def save_history():
    history_list = list(SEEN_IDS)[-2000:]
    with open(HIST_FILE, "w", encoding="utf-8") as f:
        json.dump(history_list, f, ensure_ascii=False, indent=2)

def clean_html(raw_html: str) -> str:
    cleantext = re.sub(r'<[^>]+>', ' ', raw_html)
    cleantext = html.unescape(cleantext)
    return " ".join(cleantext.split())

def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "false"
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"User-Agent": "JobMonitor3DBot/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            pass
        logging.info("📱 Alerta enviada con éxito a Telegram.")
    except Exception as e:
        logging.error(f"Error enviando mensaje a Telegram: {e}")

def matches_criteria(text: str, is_curated_job_board: bool = False) -> bool:
    has_3d = any(r.search(text) for r in REGEX_3D)
    if is_curated_job_board:
        return has_3d
    has_hiring = any(r.search(text) for r in REGEX_HIRING)
    return has_3d and has_hiring

def fetch_json(url: str):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0.0.0 Safari/537.36"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode('utf-8'))

def check_all_sources():
    logging.info("🔍 Comprobando bolsas de empleo y comunidades...")
    new_found = 0

    for src in SOURCES:
        name = src["name"]
        url = src["url"]
        stype = src["type"]

        try:
            data = fetch_json(url)

            if stype == "mastodon":
                for post in data:
                    item_id = f"masto_{post.get('id')}"
                    if item_id in SEEN_IDS:
                        continue

                    content = clean_html(post.get("content", ""))
                    post_url = post.get("url", "")

                    if matches_criteria(content, is_curated_job_board=False):
                        new_found += 1
                        snippet = (content[:280] + '...') if len(content) > 280 else content
                        
                        msg = (
                            f"🚨 <b>¡NUEVA OFERTA / OPORTUNIDAD 3D!</b>\n\n"
                            f"📌 <b>Fuente:</b> {name}\n"
                            f"📝 <b>Detalle:</b>\n{snippet}\n\n"
                            f"🔗 <b>Enlace:</b>\n{post_url}\n\n"
                            f"💡 <i>¡Sé de los primeros en responder con tu portafolio!</i>"
                        )
                        send_telegram(msg)
                    
                    SEEN_IDS.add(item_id)

            elif stype == "remotive":
                jobs = data.get("jobs", [])
                for job in jobs:
                    item_id = f"remotive_{job.get('id')}"
                    if item_id in SEEN_IDS:
                        continue

                    title = job.get("title", "")
                    company = job.get("company_name", "")
                    job_url = job.get("url", "")
                    desc = clean_html(job.get("description", ""))
                    full_text = f"{title} {desc}"

                    if matches_criteria(full_text, is_curated_job_board=True):
                        new_found += 1
                        msg = (
                            f"🚨 <b>¡NUEVA OFERTA 3D DETECTADA!</b>\n\n"
                            f"📌 <b>Fuente:</b> {name}\n"
                            f"🏢 <b>Empresa:</b> {company}\n"
                            f"📝 <b>Puesto:</b> {title}\n\n"
                            f"🔗 <b>Postularse:</b>\n{job_url}\n\n"
                            f"💡 <i>¡Envía tu portafolio y carta de presentación!</i>"
                        )
                        send_telegram(msg)

                    SEEN_IDS.add(item_id)

            elif stype == "remoteok":
                # La primera entrada de remoteok suele ser legal/metadata
                jobs = data[1:] if isinstance(data, list) and len(data) > 1 else []
                for job in jobs:
                    item_id = f"remoteok_{job.get('id')}"
                    if item_id in SEEN_IDS:
                        continue

                    title = job.get("position", "")
                    company = job.get("company", "")
                    job_url = job.get("url", "")
                    tags = " ".join(job.get("tags", []))
                    desc = clean_html(job.get("description", ""))
                    full_text = f"{title} {tags} {desc}"

                    if matches_criteria(full_text, is_curated_job_board=True):
                        new_found += 1
                        msg = (
                            f"🚨 <b>¡NUEVA OFERTA 3D / GAME ART!</b>\n\n"
                            f"📌 <b>Fuente:</b> {name}\n"
                            f"🏢 <b>Empresa:</b> {company}\n"
                            f"📝 <b>Puesto:</b> {title}\n\n"
                            f"🔗 <b>Postularse:</b>\n{job_url}\n\n"
                            f"💡 <i>¡Revisa los requisitos y postula con tu web!</i>"
                        )
                        send_telegram(msg)

                    SEEN_IDS.add(item_id)

        except Exception as e:
            logging.error(f"Error revisando {name}: {e}")

    if new_found > 0:
        save_history()
    logging.info(f"Comprobación finalizada. Nuevas ofertas enviadas: {new_found}")

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )
    logging.info("🤖 Job Monitor 3D Activo y Vigilando...")

    # Ejecutar una primera revisión al iniciar
    check_all_sources()

    # Repetir revisión cada 5 minutos
    schedule.every(5).minutes.do(check_all_sources)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
