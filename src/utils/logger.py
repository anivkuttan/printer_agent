# Setup logging once (probably in your app init)
import logging
from logging.handlers import RotatingFileHandler
import os


log_dir = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "print_logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "print.log")

# 5MB per file, keep 5 backups
handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[handler]
)

logger = logging.getLogger("printer_logger")
