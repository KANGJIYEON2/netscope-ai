#!/usr/bin/env python3
"""NETSCOPE log agent — tails a log file and POSTs interesting lines to /ingest.

Config via env (CLI flags override):
    NETSCOPE_API_URL     default http://127.0.0.1:8000/ingest
    NETSCOPE_API_KEY     sent as X-API-Key (required if backend INGEST_API_KEY set)
    NETSCOPE_OFFSET_DIR  default ~/.netscope-agent

Reliability: the byte offset only advances after a SUCCESSFUL POST, so a backend
outage no longer loses logs — the same range is retried on the next tick.
"""
import argparse
import os
import re
import socket
import time
from datetime import datetime, UTC

import requests

# =========================
# CONFIG (env, CLI overrides)
# =========================
DEFAULT_API_URL = os.getenv("NETSCOPE_API_URL", "http://127.0.0.1:8000/ingest")
DEFAULT_API_KEY = os.getenv("NETSCOPE_API_KEY")
DEFAULT_OFFSET_DIR = os.getenv(
    "NETSCOPE_OFFSET_DIR",
    os.path.join(os.path.expanduser("~"), ".netscope-agent"),
)

CONTROL_CHARS = re.compile(r"[\x00-\x1F\x7F-\x9F]")
LEVEL_REGEX = re.compile(r"\b(ERROR|WARN|INFO)\b", re.IGNORECASE)


# =========================
# UTIL
# =========================
def hostname() -> str:
    return socket.gethostname()


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def normalize(line: str) -> str:
    """BOM / 제어문자 제거 (Windows, PowerShell 대응)."""
    line = line.replace("﻿", "")
    line = CONTROL_CHARS.sub("", line)
    return line.strip()


def detect_level(line: str) -> str:
    m = LEVEL_REGEX.search(line)
    return m.group(1).upper() if m else "DEBUG"


def _offset_path(offset_dir: str, log_path: str) -> str:
    os.makedirs(offset_dir, exist_ok=True)
    safe_name = re.sub(r"[^\w]", "_", os.path.abspath(log_path))
    return os.path.join(offset_dir, f"{safe_name}.offset")


def load_offset(offset_dir: str, log_path: str) -> int:
    try:
        with open(_offset_path(offset_dir, log_path), "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def save_offset(offset_dir: str, log_path: str, offset: int) -> None:
    with open(_offset_path(offset_dir, log_path), "w") as f:
        f.write(str(offset))


def is_interesting(line: str) -> bool:
    """Agent-side Rule Engine v0."""
    if detect_level(line) in ("ERROR", "WARN"):
        return True
    if re.search(r"\bTIMEOUT\b|\bTIMED\s+OUT\b", line, re.IGNORECASE):
        return True
    if re.search(r"\b5\d\d\b", line):
        return True
    return False


# =========================
# SEND
# =========================
def send_logs(*, api_url: str, api_key: str | None, lines: list[str],
              tenant_id: str, project_id: str) -> bool:
    """POST /ingest — returns True only on a 2xx response."""
    headers = {
        "X-Tenant-ID": tenant_id,
        "X-Project-ID": project_id,
        "X-Agent-ID": hostname(),
    }
    if api_key:
        headers["X-API-Key"] = api_key

    print(f"\n[AGENT] ▶ POST {api_url}  ({len(lines)} lines)")
    try:
        r = requests.post(api_url, json={"logs": lines}, headers=headers, timeout=5)
        r.raise_for_status()
        print("[AGENT] status:", r.status_code)
        for l in lines:
            print(f"[SENT] {l[:120]}")
        return True
    except Exception as e:
        print("[FAILED]", repr(e), "→ offset 유지, 다음 틱에 재시도")
        return False


# =========================
# TAIL
# =========================
def tail_file(*, path: str, source: str, tenant_id: str, project_id: str,
              api_url: str, api_key: str | None, offset_dir: str):
    print("[BOOT] NETSCOPE AGENT STARTED")
    print("[BOOT] watching:", path)
    print("[BOOT] source:", source, "| tenant:", tenant_id, "| project:", project_id)
    print("[BOOT] api:", api_url, "| auth:", "on" if api_key else "off")

    last_size = load_offset(offset_dir, path)
    print(f"[BOOT] resume offset: {last_size} bytes\n")

    while True:
        try:
            if not os.path.exists(path):
                print("[WAIT] log file not found")
                time.sleep(1)
                continue

            current_size = os.path.getsize(path)

            # Log rotation: file truncated
            if current_size < last_size:
                print("[ROTATE] file truncated, resetting offset")
                last_size = 0
                save_offset(offset_dir, path, 0)

            if current_size > last_size:
                with open(path, "r", errors="ignore") as f:
                    f.seek(last_size)
                    new_data = f.read()

                batch = []
                for raw_line in new_data.splitlines():
                    line = normalize(raw_line)
                    if line and is_interesting(line):
                        batch.append(line)

                # 전송 성공 시에만 offset 전진 (실패하면 다음 틱에 같은 범위 재시도)
                sent_ok = True
                if batch:
                    sent_ok = send_logs(
                        api_url=api_url, api_key=api_key, lines=batch,
                        tenant_id=tenant_id, project_id=project_id,
                    )

                if sent_ok:
                    last_size = current_size
                    save_offset(offset_dir, path, last_size)

        except Exception as e:
            print("[AGENT ERROR]", repr(e))

        time.sleep(1)


# =========================
# MAIN
# =========================
def main():
    parser = argparse.ArgumentParser("NETSCOPE Agent (tail mode)")
    parser.add_argument("--path", required=True, help="log file path")
    parser.add_argument("--source", default="unknown-service", help="service name")
    parser.add_argument("--tenant", required=True, help="tenant id")
    parser.add_argument("--project", required=True, help="project id")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="ingest URL (env NETSCOPE_API_URL)")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help="X-API-Key (env NETSCOPE_API_KEY)")
    parser.add_argument("--offset-dir", default=DEFAULT_OFFSET_DIR, help="offset dir (env NETSCOPE_OFFSET_DIR)")
    args = parser.parse_args()

    tail_file(
        path=args.path,
        source=args.source,
        tenant_id=args.tenant,
        project_id=args.project,
        api_url=args.api_url,
        api_key=args.api_key,
        offset_dir=args.offset_dir,
    )


if __name__ == "__main__":
    main()
