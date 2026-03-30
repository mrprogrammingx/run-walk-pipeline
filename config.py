"""Project-wide configuration helpers.

This module loads `.env` (if present) once and provides small helpers to
read environment variables and common repo paths. Importing this module is
safe from scripts run at the repository root (it uses its own file location
to determine the repo root).
"""
from __future__ import annotations

import logging
import os
from typing import Optional

LOGGER = logging.getLogger(__name__)


REPO_ROOT = os.path.abspath(os.path.dirname(__file__))


def _load_dotenv() -> None:
    """Try to load a .env file using python-dotenv if available, otherwise
    fall back to a minimal loader that parses KEY=VALUE lines.
    """
    try:
        from dotenv import load_dotenv

        load_dotenv(dotenv_path=os.path.join(REPO_ROOT, ".env"))
        LOGGER.debug("Loaded .env via python-dotenv")
        return
    except Exception:
        LOGGER.debug("python-dotenv not available; using fallback .env parser")

    # Fallback parser
    env_path = os.path.join(REPO_ROOT, ".env")
    if not os.path.exists(env_path):
        return

    try:
        with open(env_path, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                os.environ.setdefault(key, val)
        LOGGER.debug("Loaded .env via fallback parser")
    except Exception:
        LOGGER.debug("Failed to parse .env with fallback", exc_info=True)


# Load .env on import (idempotent)
_load_dotenv()


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Return environment variable or default.

    This uses already-loaded environment (including .env values loaded on
    import). It does not attempt to re-read .env.
    """
    return os.environ.get(key, default)


def repo_path(*parts: str) -> str:
    """Return an absolute path under the repository root."""
    return os.path.join(REPO_ROOT, *parts)
