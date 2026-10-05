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
# CONFIGURACIÓN TELEGRAM Y PORTFOLIO
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).parent

TELEGRAM_BOT_TOKEN = "8958926765:AAHka_dr0e4kewtgyY-D0pgilYLx85wXO4w"
TELEGRAM_CHAT_ID = "708457190"
PORTFOLIO_URL = "https://pepm83-arch.github.io/Portfolio"

# Fuentes de ofertas
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

# 1. TÉRMINOS ARTÍSTICOS EXPLÍCITOS DE NUESTRA ESPECIALIDAD (Obligatorios)
ARTISTIC_3D_KEYWORDS = [
    r"3d\s+modeler",
    r"3d\s+modeller",
    r"3d\s+artist",
    r"3d\s+generalist",
    r"\bprops?\b",
    r"\bcharacters?\b",
    r"\benvironments?\b",
    r"\bassets?\b",
    r"\bsculptor\b",
    r"\bsculpting\b",
    r"\bminiatures?\b",
    r"\bblender\b",
    r"\bzbrush\b",
    r"hard\s+surface",
    r"modelador\s+3d",
    r"artista\s+3d"
]

# 2. TÉRMINOS ADMINISTRATIVOS / CORPORATIVOS A DESCARTAR (Lista negra estricta en el título)
EXCLUDED_TITLE_KEYWORDS = [
    r"\bmanager\b",
    r"\bdirector\b",
    r"\bassistant\b",
    r"\bstrategist\b",
    r"\brecruiter\b",
    r"\bmarketing\b",
    r"\bhr\b",
    r"\blegal\b",
    r"\bdeveloper\b",
    r"\bfrontend\b",
    r"\bbackend\b",
    r"\bengineer\b",
    r"\baccountant\b",
    r"\bsales\b",
    r"\banalyst\b",
    r"\bqa\b",
    r"\bproduct\s+owner\b",
    r"\bexecutive\b"
]

# Palabras de contratación requeridas para comunidades abiertas (Mastodon)
KEYWORDS_HIRING = [
    r"\bhiring\b",
    r"looking for",
    r"we need",
    r"\bjob\b",
    r"\bposition\b",
    r"\bfreelance\b",
    r"\bcontract\b",
    r"\bremote\b",
    r"\bpaid\b",
    r"\bbuscamos\b",
    r"se busca",
    r"\bnecesit"
]

REGEX_ARTISTIC_3D = [re.compile(k, re.IGNORECASE) for k in ARTISTIC_3D_KEYWORDS]
REGEX_EXCLUDED_TITLE = [re.compile(k, re.IGNORECASE) for k in EXCLUDED_TITLE_KEYWORDS]
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

def build_application_pitch(job_title: str) -> str:
    """Genera el mensaje de postulación listo para copiar y pegar en inglés."""
    pitch = (
        f"Hi,\n\n"
        f"I came across your opening for {job_title} and would love to collaborate with you.\n\n"
        f"I'm a 3D Generalist & Modeler specializing in Props, Characters, and Hard Surface assets with production experience. "
        f"My core workflow is built around Blender and ZBrush, optimizing models for real-time game engines/animation as well as 3D printing & miniatures.\n\n"
        f"You can review my interactive portfolio and previous work here:\n"
        f"{PORTFOLIO_URL}\n\n"
        f"I have immediate availability for remote freelance / contract work and would be happy to complete a quick art test if needed.\n\n"
        f"Looking forward to hearing from you!\n"
        f"Best regards,\n"
        f"José Miguel"
    )
    return pitch

def is_strictly_3d_art(title: str, content: str, is_curated_job_board: bool = False) -> bool:
    """Filtra estrictamente asegurando que sea un puesto de arte 3D y sin ruido corporativo."""
    # 1. Descartar si el título contiene puestos corporativos/administrativos
    if any(r.search(title) for r in REGEX_EXCLUDED_TITLE):
        return False

    full_text = f"{title} {content}"

    # 2. Exigir explícitamente términos artísticos 3D clave
    has_artistic_3d = any(r.search(full_text) for r in REGEX_ARTISTIC_3D)
    if not has_artistic_3d:
        return False

    # 3. En comunidades abiertas, asegurar que es una oferta (no alguien buscando trabajo)
    if not is_curated_job_board:
        title_lower = title.lower()
        if "[for hire]" in title_lower and "[hiring]" not in title_lower:
            return False
        has_hiring = any(r.search(full_text) for r in REGEX_HIRING)
        if not has_hiring:
            return False

    return True

def fetch_json(url: str):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0.0.0 Safari/537.36"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode('utf-8'))

def check_all_sources():
    logging.info("🔍 Comprobando bolsas de empleo con filtrado estricto de Arte 3D...")
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
                    # En Mastodon no siempre hay título separado, extraemos la primera frase como título
                    first_line = content.split(".")[0][:70] if content else "3D Artist Opportunity"

                    if is_strictly_3d_art(first_line, content, is_curated_job_board=False):
                        new_found += 1
                        snippet = (content[:250] + '...') if len(content) > 250 else content
                        pitch = build_application_pitch(first_line)

                        msg = (
                            f"🚨 <b>¡NUEVA OFERTA 3D DETECTADA!</b>\n\n"
                            f"📌 <b>Fuente:</b> {name}\n"
                            f"📝 <b>Detalle:</b>\n{html.escape(snippet)}\n\n"
                            f"🔗 <b>Enlace a la oferta:</b>\n{post_url}\n\n"
                            f"📋 <b>PITCH RÁPIDO (Copia y Pega para postularte):</b>\n"
                            f"<code>{html.escape(pitch)}</code>"
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

                    if is_strictly_3d_art(title, desc, is_curated_job_board=True):
                        new_found += 1
                        pitch = build_application_pitch(title)

                        msg = (
                            f"🚨 <b>¡NUEVA OFERTA 3D DETECTADA!</b>\n\n"
                            f"📌 <b>Fuente:</b> {name}\n"
                            f"🏢 <b>Empresa:</b> {html.escape(company)}\n"
                            f"📝 <b>Puesto:</b> {html.escape(title)}\n\n"
                            f"🔗 <b>Enlace a la oferta:</b>\n{job_url}\n\n"
                            f"📋 <b>PITCH RÁPIDO (Copia y Pega para postularte):</b>\n"
                            f"<code>{html.escape(pitch)}</code>"
                        )
                        send_telegram(msg)

                    SEEN_IDS.add(item_id)

            elif stype == "remoteok":
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
                    content = f"{tags} {desc}"

                    if is_strictly_3d_art(title, content, is_curated_job_board=True):
                        new_found += 1
                        pitch = build_application_pitch(title)

                        msg = (
                            f"🚨 <b>¡NUEVA OFERTA 3D DETECTADA!</b>\n\n"
                            f"📌 <b>Fuente:</b> {name}\n"
                            f"🏢 <b>Empresa:</b> {html.escape(company)}\n"
                            f"📝 <b>Puesto:</b> {html.escape(title)}\n\n"
                            f"🔗 <b>Enlace a la oferta:</b>\n{job_url}\n\n"
                            f"📋 <b>PITCH RÁPIDO (Copia y Pega para postularte):</b>\n"
                            f"<code>{html.escape(pitch)}</code>"
                        )
                        send_telegram(msg)

                    SEEN_IDS.add(item_id)

        except Exception as e:
            logging.error(f"Error revisando {name}: {e}")

    if new_found > 0:
        save_history()
    logging.info(f"Comprobación finalizada. Ofertas válidas de Arte 3D enviadas: {new_found}")

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )
    logging.info("🤖 Job Monitor 3D Activo (Filtro Estricto + Asistente de Postulación)...")

    # Ejecutar primera revisión al iniciar
    check_all_sources()

    # Repetir revisión cada 5 minutos en local
    schedule.every(5).minutes.do(check_all_sources)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
