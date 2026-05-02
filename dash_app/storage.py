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


@dataclass(frozen=True)
class UploadedCsv:
    name: str
    object_path: str
    size: int | None = None
    created_at: str = ""


@dataclass(frozen=True)
class UploadListResult:
    enabled: bool
    ok: bool
    message: str
    items: tuple[UploadedCsv, ...] = ()


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


def _headers(content_type: str = "application/json") -> dict[str, str]:
    _, key, _, _ = _config()
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": content_type,
    }


def _with_prefix(name: str, prefix: str) -> str:
    normalized = name.strip("/")
    if normalized.startswith(f"{prefix}/"):
        return normalized
    return f"{prefix}/{normalized}" if prefix else normalized


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
    headers = _headers("text/csv; charset=utf-8") | {"x-upsert": "false"}

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


def list_csv_uploads(limit: int = 25) -> UploadListResult:
    """Return recent CSV objects from the configured upload prefix."""
    if not is_enabled():
        return UploadListResult(
            enabled=False,
            ok=False,
            message="Supabase storage is not configured, so there are no saved CSVs to list.",
        )

    url, _, bucket, prefix = _config()
    endpoint = f"{url}/storage/v1/object/list/{bucket}"
    payload = {
        "prefix": prefix,
        "limit": limit,
        "offset": 0,
        "sortBy": {"column": "created_at", "order": "desc"},
    }

    try:
        response = requests.post(endpoint, headers=_headers(), json=payload, timeout=10)
        if response.status_code >= 400:
            return UploadListResult(
                enabled=True,
                ok=False,
                message=f"Could not list Supabase uploads: {response.status_code} {response.text[:180]}",
            )
        rows = response.json()
    except (ValueError, requests.RequestException) as exc:
        return UploadListResult(
            enabled=True,
            ok=False,
            message=f"Could not list Supabase uploads: {exc}",
        )

    items: list[UploadedCsv] = []
    for row in rows:
        name = str(row.get("name", ""))
        if not name or not name.lower().endswith(".csv"):
            continue
        metadata = row.get("metadata") or {}
        items.append(
            UploadedCsv(
                name=Path(name).name,
                object_path=_with_prefix(name, prefix),
                size=metadata.get("size"),
                created_at=str(row.get("created_at") or row.get("updated_at") or ""),
            )
        )

    return UploadListResult(
        enabled=True,
        ok=True,
        message=f"Showing {len(items)} saved CSV upload{'s' if len(items) != 1 else ''}.",
        items=tuple(items),
    )


def delete_csv(object_path: str) -> StorageResult:
    """Delete one uploaded CSV from Supabase Storage.

    Deletion is intentionally limited to CSV files inside the configured upload
    prefix so a mis-click cannot remove unrelated bucket content.
    """
    if not is_enabled():
        return StorageResult(
            enabled=False,
            ok=False,
            message="Supabase storage is not configured, so there is nothing to delete.",
            object_path=object_path,
        )

    url, _, bucket, prefix = _config()
    normalized = object_path.strip("/")
    if not normalized.startswith(f"{prefix}/") or not normalized.lower().endswith(".csv"):
        return StorageResult(
            enabled=True,
            ok=False,
            message="Refused to delete because this file is outside the configured CSV upload folder.",
            object_path=object_path,
        )

    endpoint = f"{url}/storage/v1/object/{bucket}"
    try:
        response = requests.delete(endpoint, headers=_headers(), json={"prefixes": [normalized]}, timeout=10)
        if response.status_code >= 400:
            return StorageResult(
                enabled=True,
                ok=False,
                message=f"Supabase delete failed: {response.status_code} {response.text[:180]}",
                object_path=normalized,
            )
    except requests.RequestException as exc:
        return StorageResult(
            enabled=True,
            ok=False,
            message=f"Supabase delete failed: {exc}",
            object_path=normalized,
        )

    return StorageResult(
        enabled=True,
        ok=True,
        message=f"Deleted {normalized}",
        object_path=normalized,
    )
