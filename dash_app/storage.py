"""Optional Supabase Storage persistence for uploaded donor CSVs."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests


DEFAULT_BUCKET = "riverkeeper-uploads"
DEFAULT_PREFIX = "uploads"
ROOT = Path(__file__).resolve().parents[1]


def load_local_env(path: Path = ROOT / ".env") -> None:
    if not path.exists():
        return

    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_env()


@dataclass(frozen=True)
class StorageResult:
    enabled: bool
    ok: bool
    message: str
    object_path: str = ""


def is_enabled() -> bool:
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"))


def _config() -> tuple[str, str, str, str]:
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    bucket = os.getenv("SUPABASE_STORAGE_BUCKET", DEFAULT_BUCKET)
    prefix = os.getenv("SUPABASE_STORAGE_PREFIX", DEFAULT_PREFIX).strip("/")
    return url, key, bucket, prefix


def _safe_filename(filename: str | None) -> str:
    fallback = "uploaded-donors.csv"
    name = Path(filename or fallback).name
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-")
    return safe or fallback


def upload_csv(contents: bytes, filename: str | None) -> StorageResult:
    """Persist a CSV upload to Supabase Storage when configured.

    The app still works without Supabase; this function returns a disabled
    result when env vars are missing so the UI can explain what happened.
    """
    if not is_enabled():
        return StorageResult(
            enabled=False,
            ok=False,
            message="Stored for this session only. Supabase storage is not configured.",
        )

    url, key, bucket, prefix = _config()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    object_path = f"{prefix}/{timestamp}-{_safe_filename(filename)}"
    encoded_path = quote(object_path, safe="/")
    endpoint = f"{url}/storage/v1/object/{bucket}/{encoded_path}"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "text/csv; charset=utf-8",
        "x-upsert": "false",
    }

    try:
        response = requests.post(endpoint, headers=headers, data=contents, timeout=30)
        if response.status_code >= 400:
            return StorageResult(
                enabled=True,
                ok=False,
                message=f"Upload parsed, but Supabase returned {response.status_code}: {response.text[:180]}",
                object_path=object_path,
            )
    except requests.RequestException as exc:
        return StorageResult(
            enabled=True,
            ok=False,
            message=f"Upload parsed, but Supabase storage failed: {exc}",
            object_path=object_path,
        )

    return StorageResult(
        enabled=True,
        ok=True,
        message=f"Saved to Supabase Storage: {object_path}",
        object_path=object_path,
    )
