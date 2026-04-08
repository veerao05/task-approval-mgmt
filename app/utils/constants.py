from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

LOGS_DIR = str(BASE_DIR / "logs")
LOGGING_CONFIG_FILE = str(BASE_DIR / "config" / "logging.ini")
