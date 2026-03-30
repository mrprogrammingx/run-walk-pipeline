"""Clean downloader for the Kaggle dataset used by this project.

This module provides a small, well-typed API and a CLI entrypoint to
download the `vmalyi/run-or-walk` dataset into the repository's
`data/raw/` directory. It intentionally keeps external dependencies
minimal and falls back to reading a local `.env` file if environment
variables are not set.

Functions:
 - download_dataset(output_dir: str) -> list[str]

Usage:
    python -m ingestion.download_kaggle
"""

from __future__ import annotations

import base64
import json
import logging
import os
import subprocess
from typing import List, Optional, Tuple


LOGGER = logging.getLogger(__name__)
DATASET = "vmalyi/run-or-walk"


def _load_env_fallback(repo_root: str) -> None:
    """Load simple KEY=VALUE pairs from a .env file into environment.

    Only sets variables that are not already present in os.environ.
    """
    env_path = os.path.join(repo_root, ".env")
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
                val = val.strip().strip("\"\'")
                os.environ.setdefault(key, val)
    except Exception:
        LOGGER.debug("Failed to load .env fallback", exc_info=True)


def _parse_kaggle_token(token: str) -> Tuple[str, str]:
    """Parse project token into (username, api_key).

    Expect token like 'KGAT_<base64(username:api_key)>'. If parsing fails,
    return ('kaggleapi', token) so the token is used as the key.
    """
    if not token:
        raise ValueError("empty kaggle token")

    prefix = "KGAT_"
    if token.startswith(prefix):
        try:
            raw = base64.b64decode(token[len(prefix):]).decode("utf-8")
            if ":" in raw:
                username, api_key = raw.split(":", 1)
                return username, api_key
        except Exception:
            LOGGER.debug("Could not decode KGAT token", exc_info=True)

    # Fallback
    return "kaggleapi", token


def _write_kaggle_config(username: str, key: str) -> None:
    cfg_dir = os.path.expanduser("~/.kaggle")
    os.makedirs(cfg_dir, exist_ok=True)
    cfg_path = os.path.join(cfg_dir, "kaggle.json")
    data = {"username": username, "key": key}
    with open(cfg_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    try:
        os.chmod(cfg_path, 0o600)
    except Exception:
        LOGGER.debug("Could not chmod kaggle.json", exc_info=True)


def _run_kaggle_cli(output_dir: str, dataset: str) -> subprocess.CompletedProcess:
    cmd = ["kaggle", "datasets", "download", "-d", dataset, "-p", output_dir, "--unzip"]
    LOGGER.debug("Running command: %s", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True)


def _list_files(path: str) -> List[str]:
    try:
        return sorted(os.listdir(path))
    except Exception:
        return []


def download_dataset(output_dir: str, dataset: str = DATASET) -> List[str]:
    """Download `dataset` into `output_dir` and return list of downloaded items.

    The function attempts to read `KAGGLE_API_TOKEN` from the environment. If
    missing, it will attempt to load a `.env` file in the repository root.
    """
    # ensure environment has token (config module already loads .env on import)
    from config import get_env

    token = get_env("KAGGLE_API_TOKEN")

    if not token:
        raise RuntimeError("KAGGLE_API_TOKEN not found in environment or .env")

    username, api_key = _parse_kaggle_token(token)
    _write_kaggle_config(username, api_key)

    os.makedirs(output_dir, exist_ok=True)
    LOGGER.info("Downloading %s to %s", dataset, output_dir)

    try:
        proc = _run_kaggle_cli(output_dir, dataset)
    except FileNotFoundError as exc:
        raise RuntimeError("kaggle CLI not found on PATH") from exc

    if proc.returncode != 0:
        LOGGER.error("kaggle CLI failed: %s", proc.stderr or proc.stdout)
        raise RuntimeError("kaggle download failed")

    files = _list_files(output_dir)
    LOGGER.info("Downloaded %d item(s)", len(files))
    return files


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    out = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")
    # repo-wide .env is already loaded by config on import
    from config import repo_path
    out = repo_path("data", "raw")

    try:
        files = download_dataset(out)
        for f in files:
            path = os.path.join(out, f)
            if os.path.isfile(path):
                LOGGER.info("  - %s (%d bytes)", f, os.path.getsize(path))
            else:
                LOGGER.info("  - %s/ (directory)", f)
        return 0
    except Exception as exc:
        LOGGER.error("Download failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
