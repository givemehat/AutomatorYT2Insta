import logging
import sys
from typing import Optional, Dict, Any
from app.database import SessionLocal
from app.models.system_log import SystemLog

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("AutomatorYT2Insta")

def log_event(
    level: str,
    source: str,
    message: str,
    context_data: Optional[Dict[str, Any]] = None
) -> None:
    """Logs structured event to stdout and persists to database audit log."""
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(f"[{source.upper()}] {message}")
    
    try:
        with SessionLocal() as db:
            db_log = SystemLog(
                level=level.upper(),
                source=source,
                message=message,
                context_data=context_data
            )
            db.add(db_log)
            db.commit()
    except Exception as e:
        logger.warning(f"Could not persist log to database: {e}")
