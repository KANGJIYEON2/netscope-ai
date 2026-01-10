#!/usr/bin/env python3
import argparse
import time
import socket
import re
import requests
import os
from datetime import datetime, UTC

# 중요 v2에 붙이기

# =========================
# CONFIG
# =========================
API_URL = "http://127.0.0.1:8000/logs"

# 로그 필터 룰 (Agent-side Rule v0)
KEYWORDS = re.compile(
    r"\b(ERROR|WARN)\b|\bTIMEOUT\b|\bTIMED\s+OUT\b|\b5\d\d\b",
    re.IGNORECASE,
)

# 제어문자 제거
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
    """
    BOM / 제어문자 제거 (Windows, PowerShell 대응)
    """
    line = line.replace("\ufeff", "")
    line = CONTROL_CHARS.sub("", line)
    return line.strip()

def detect_level(line: str) -> str:
    m = LEVEL_REGEX.search(line)
    if not m:
        return "DEBUG"
    return m.group(1).upper()

def is_interesting(line: str) -> bool:
    """
    Agent-side Rule Engine v0
    """
    level = detect_level(line)

    if level in ("ERROR", "WARN"):
        return True

    if re.search(r"\bTIMEOUT\b|\bTIMED\s+OUT\b", line, re.IGNORECASE):
        return True

    if re.search(r"\b5\d\d\b", line):
        return True

    return False

# =========================
# SEND
# =========================
def send_log(
    *,
    line: str,
    source: str,
    tenant_id: str,
    project_id: str,
):
    payload = {
        "source": source,
        "message": line,
        "level": detect_level(line),
        "timestamp": now_iso(),
        "host": hostname(),
    }

    headers = {
        "X-Tenant-ID": tenant_id,
        "X-Project-ID": project_id,
    }

    print("\n[AGENT] ▶ POST /logs")
    print("[AGENT] headers:", headers)
    print("[AGENT] payload:", payload)

    try:
        r = requests.post(
            API_URL,
            json=payload,
            headers=headers,
            timeout=3,
        )
        print("[AGENT] status:", r.status_code)
        r.raise_for_status()
        print(f"[SENT] {payload['level']} {line}")
    except Exception as e:
        print("[FAILED]", repr(e))

# =========================
# TAIL
# =========================
def tail_file(
    *,
    path: str,
    source: str,
    tenant_id: str,
    project_id: str,
):
    print("[BOOT] NETSCOPE AGENT STARTED")
    print("[BOOT] watching:", path)
    print("[BOOT] source:", source)
    print("[BOOT] tenant:", tenant_id)
    print("[BOOT] project:", project_id)
    print("[BOOT] api:", API_URL)
    print()

    last_size = 0

    while True:
        try:
            if not os.path.exists(path):
                print("[WAIT] log file not found")
                time.sleep(1)
                continue

            current_size = os.path.getsize(path)

            if current_size > last_size:
                with open(path, "r", errors="ignore") as f:
                    f.seek(last_size)
                    new_data = f.read()

                print(f"[DEBUG] new bytes detected: {current_size - last_size}")

                for raw_line in new_data.splitlines():
                    line = normalize(raw_line)

                    if not line:
                        continue

                    print("[DEBUG] normalized:", line)

                    if is_interesting(line):
                        print("[DEBUG] ✔ rule matched")
                        send_log(
                            line=line,
                            source=source,
                            tenant_id=tenant_id,
                            project_id=project_id,
                        )
                    else:
                        print("[DEBUG] ✘ ignored")

                last_size = current_size

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

    # ✅ 멀티 테넌트 식별
    parser.add_argument("--tenant", required=True, help="tenant id")
    parser.add_argument("--project", required=True, help="project id")

    args = parser.parse_args()

    tail_file(
        path=args.path,
        source=args.source,
        tenant_id=args.tenant,
        project_id=args.project,
    )

if __name__ == "__main__":
    main()
