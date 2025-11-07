import logging

import requests
from sqlalchemy import Engine
from sqlmodel import Session, select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.core.config import settings
from app.core.db import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def init(db_engine: Engine) -> None:
    try:
        with Session(db_engine) as session:
            # Try to create session to check if DB is awake
            session.exec(select(1))
    except Exception as e:
        logger.error(e)
        raise e


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def check_ollama() -> None:
    """Check if Ollama service is accessible."""
    try:
        response = requests.get(
            f"{settings.OLLAMA_HOST}/api/tags",
            timeout=5
        )
        response.raise_for_status()
        logger.info(f"✓ Ollama service is accessible at {settings.OLLAMA_HOST}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"✗ Cannot connect to Ollama at {settings.OLLAMA_HOST}")
        raise e
    except requests.exceptions.Timeout as e:
        logger.error(f"✗ Ollama request timed out after 5 seconds")
        raise e
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Error connecting to Ollama: {e}")
        raise e


def main() -> None:
    logger.info("Initializing service")
    init(engine)
    logger.info("Service finished initializing")

    logger.info("Checking Ollama connectivity")
    check_ollama()
    logger.info("Ollama connectivity check passed")


if __name__ == "__main__":
    main()
