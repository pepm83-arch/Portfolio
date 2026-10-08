import sys
import logging
from job_monitor import check_all_sources

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )
    logging.info("🚀 Ejecutando revisión puntual de ofertas en la nube (RSS Ampliados)...")
    try:
        check_all_sources()
        logging.info("✅ Revisión completada con éxito.")
    except Exception as e:
        logging.error(f"❌ Error durante la revisión: {e}")
        sys.exit(1)
