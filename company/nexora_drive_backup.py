"""Google Drive backup helpers for the private Nexora HQ.

All credentials are server-side environment variables. This module deliberately
fails closed when OAuth is not configured and never starts agent execution.
"""
from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

TOKEN_URL = "https://oauth2.googleapis.com/token"
DRIVE_API = "https://www.googleapis.com/drive/v3"
UPLOAD_API = "https://www.googleapis.com/upload/drive/v3/files"


class DriveBackupError(RuntimeError):
    pass


def _config() -> dict[str, str]:
    keys = {
        "client_id": "GOOGLE_DRIVE_CLIENT_ID",
        "client_secret": "GOOGLE_DRIVE_CLIENT_SECRET",
        "refresh_token": "GOOGLE_DRIVE_REFRESH_TOKEN",
        "folder_id": "GOOGLE_DRIVE_FOLDER_ID",
    }
    values = {k: os.environ.get(v, "").strip() for k, v in keys.items()}
    missing = [k for k, v in values.items() if not v]
    if missing:
        raise DriveBackupError("Google Drive OAuth is not configured: " + ", ".join(missing))
    return values


def _request(url: str, *, method: str = "GET", headers: dict | None = None,
             data: bytes | None = None, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        # Do not propagate response bodies, which could contain sensitive data.
        raise DriveBackupError(f"Google Drive request failed with HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError) as exc:
        raise DriveBackupError(f"Google Drive request failed: {type(exc).__name__}") from None


def _access_token(config: dict[str, str]) -> str:
    body = urllib.parse.urlencode({
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "refresh_token": config["refresh_token"],
        "grant_type": "refresh_token",
    }).encode()
    try:
        result = json.loads(_request(TOKEN_URL, method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"}, data=body))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise DriveBackupError("Google OAuth returned an unreadable response") from None
    token = result.get("access_token")
    if not token:
        raise DriveBackupError("Google OAuth did not issue an access token; check consent and credentials")
    return token


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": "Bearer " + token}


def drive_status() -> dict:
    try:
        config = _config()
        token = _access_token(config)
        query = urllib.parse.urlencode({
            "q": "'" + config["folder_id"].replace("'", "\\'") + "' in parents and trashed = false",
            "pageSize": "1",
            "fields": "files(id,name,mimeType)",
        })
        data = json.loads(_request(DRIVE_API + "/files?" + query, headers=_headers(token)))
        return {"configured": True, "connected": True, "backup_count_sample": len(data.get("files", []))}
    except DriveBackupError as exc:
        return {"configured": False if "not configured" in str(exc) else True,
                "connected": False, "error": str(exc)}


def create_backup(db_path: str | Path) -> dict:
    """Create a consistent SQLite snapshot and upload it into the configured Drive folder."""
    config = _config()
    token = _access_token(config)
    source = Path(db_path)
    if not source.exists():
        raise DriveBackupError("HQ database does not exist yet; nothing to back up")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"nexora-hq-backup-{stamp}-{uuid.uuid4().hex[:8]}.sqlite3"
    with tempfile.TemporaryDirectory(prefix="nexora-backup-") as temp:
        snapshot = Path(temp) / name
        with sqlite3.connect(str(source), timeout=10) as src, sqlite3.connect(str(snapshot)) as dst:
            src.backup(dst)
            check = dst.execute("PRAGMA integrity_check").fetchone()[0]
            if check != "ok":
                raise DriveBackupError("SQLite integrity check failed; backup was not uploaded")
        payload = snapshot.read_bytes()
    boundary = "nexora_" + uuid.uuid4().hex
    metadata = json.dumps({"name": name, "mimeType": "application/vnd.sqlite3",
                           "parents": [config["folder_id"]],
                           "description": "Nexora HQ SQLite snapshot; generated " + stamp}).encode()
    body = (b"--" + boundary.encode() + b"\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
            + metadata + b"\r\n--" + boundary.encode()
            + b"\r\nContent-Type: application/vnd.sqlite3\r\n\r\n" + payload
            + b"\r\n--" + boundary.encode() + b"--")
    response = _request(UPLOAD_API + "?uploadType=multipart&fields=id,name,createdTime,size",
        method="POST", headers={**_headers(token),
        "Content-Type": "multipart/related; boundary=" + boundary,
        "Content-Length": str(len(body))}, data=body, timeout=60)
    result = json.loads(response)
    if not result.get("id"):
        raise DriveBackupError("Google Drive did not confirm the backup file ID")
    return {"id": result["id"], "name": result.get("name", name),
            "created_time": result.get("createdTime"), "size": result.get("size"),
            "status": "uploaded"}


def list_backups(limit: int = 10) -> list[dict]:
    config = _config()
    token = _access_token(config)
    query = urllib.parse.urlencode({
        "q": "'" + config["folder_id"].replace("'", "\\'") + "' in parents and trashed = false and name contains 'nexora-hq-backup-'",
        "pageSize": str(max(1, min(int(limit), 50))),
        "orderBy": "createdTime desc",
        "fields": "files(id,name,createdTime,size,mimeType)",
    })
    data = json.loads(_request(DRIVE_API + "/files?" + query, headers=_headers(token)))
    return data.get("files", [])


def restore_backup(file_id: str, db_path: str | Path) -> dict:
    """Restore only a recognized backup, and refuse to overwrite a newer current DB."""
    if not file_id or len(file_id) > 200 or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in file_id):
        raise DriveBackupError("Invalid Drive file ID")
    config = _config()
    token = _access_token(config)
    files = list_backups(50)
    entry = next((f for f in files if f.get("id") == file_id and f.get("name", "").startswith("nexora-hq-backup-")), None)
    if not entry:
        raise DriveBackupError("Restore refused: file is not a listed Nexora HQ backup in the configured folder")
    source = Path(db_path)
    if source.exists() and entry.get("createdTime"):
        current_mtime = datetime.fromtimestamp(source.stat().st_mtime, timezone.utc)
        backup_time = datetime.fromisoformat(entry["createdTime"].replace("Z", "+00:00"))
        if current_mtime > backup_time:
            raise DriveBackupError("Restore refused: current database is newer than this backup; create a fresh backup or explicitly resolve the conflict")
    raw = _request(DRIVE_API + "/files/" + urllib.parse.quote(file_id) + "?alt=media", headers=_headers(token), timeout=60)
    source.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nexora-restore-") as temp:
        candidate = Path(temp) / "candidate.sqlite3"
        candidate.write_bytes(raw)
        try:
            with sqlite3.connect(str(candidate)) as con:
                integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
                tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if integrity != "ok" or not {"tasks", "approvals", "audit"}.issubset(tables):
                raise DriveBackupError("Restore refused: backup failed integrity/schema checks")
            source.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(str(candidate)) as src, sqlite3.connect(str(source)) as dst:
                src.backup(dst)
        except sqlite3.DatabaseError:
            raise DriveBackupError("Restore refused: file is not a valid Nexora HQ database") from None
    return {"status": "restored", "file_id": file_id, "name": entry["name"],
            "restored_at": datetime.now(timezone.utc).isoformat()}
