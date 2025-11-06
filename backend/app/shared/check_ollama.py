"""Check Ollama service connectivity before starting the application."""

import logging
import sys
import time

import requests

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 3
TIMEOUT_SECONDS = 5


def check_ollama_connectivity() -> bool:
    """Check if Ollama service is accessible.

    Returns:
        True if Ollama is accessible, False otherwise
    """
    try:
        # Try to access the Ollama API
        response = requests.get(
            f"{settings.OLLAMA_HOST}/api/tags", timeout=TIMEOUT_SECONDS
        )
        response.raise_for_status()
        logger.info(f"✓ Ollama service is accessible at {settings.OLLAMA_HOST}")
        return True
    except requests.exceptions.ConnectionError:
        logger.error(f"✗ Cannot connect to Ollama at {settings.OLLAMA_HOST}")
        return False
    except requests.exceptions.Timeout:
        logger.error(f"✗ Ollama request timed out after {TIMEOUT_SECONDS} seconds")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Error connecting to Ollama: {e}")
        return False


def main() -> None:
    """Check Ollama connectivity with retries."""
    logger.info(f"Checking Ollama connectivity at {settings.OLLAMA_HOST}")
    logger.info(f"Will retry {MAX_RETRIES} times with {TIMEOUT_SECONDS}s timeout")

    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(f"Attempt {attempt}/{MAX_RETRIES}...")

        if check_ollama_connectivity():
            logger.info("Ollama connectivity check passed")
            sys.exit(0)

        if attempt < MAX_RETRIES:
            logger.warning("Retrying in 2 seconds...")
            time.sleep(2)

    logger.error(
        f"Failed to connect to Ollama after {MAX_RETRIES} attempts. "
        "Please ensure Ollama service is running and accessible."
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
