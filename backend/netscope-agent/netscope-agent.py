#!/usr/bin/env python3
import argparse
import time
import socket
import re
import requests
import os
from datetime import datetime, UTC

# =========================
# CONFIG
# =========================
API_URL = "http://127.0.0.1:8000/logs"

# 로그 필터 룰 (실무 기준)
KEYWORDS = re.compile(
    r"\b(ERROR|WARN)\b|\bTIMEOUT\b|\bTIMED\s+OUT\b|\b5\d\d\b",
    re.IGNORECASE,
)

# 제어문자 제거용
CONTROL_CHARS = re.compile(r"[\x00-\x1F\x7F-\x9F]")

LEVEL_REGEX = re.compile(r"\b(ERROR|WARN|INFO)\b", re.IGNORECASE)

# =========================
# UTIL
# =========================
def hostname():
    return socket.gethostname()

def now_iso():
    return datetime.now(UTC).isoformat()

def normalize(line: str) -> str:
    """
    PowerShell / Windows BOM / 제어문자 제거
    """
    line = line.replace("\ufeff", "")        # BOM 제거
    line = CONTROL_CHARS.sub("", line)        # 제어문자 제거
    return line.strip()

def detect_level(line: str) -> str:
    m = LEVEL_REGEX.search(line)
    if not m:
        return "DEBUG"
    return m.group(1).upper()

def is_interesting(line: str) -> bool:
    """
    Rule Engine v0 (Agent-side)
    """
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
def send_log(line: str, source: str):
    payload = {
        "source": source,
        "message": line,
        "level": detect_level(line),
        "timestamp": now_iso(),
        "host": hostname(),
    }

    print("\n[AGENT] ▶ POST /logs")
    print("[AGENT] payload:", payload)

    try:
        r = requests.post(API_URL, json=payload, timeout=3)
        print("[AGENT] status:", r.status_code)
        print("[AGENT] response:", r.text)
        r.raise_for_status()
        print(f"[SENT] {payload['level']} {line}")
    except Exception as e:
        print("[FAILED]", repr(e))

# =========================
# TAIL
# =========================
def tail_file(path: str, source: str):
    print("[BOOT] NETSCOPE AGENT STARTED")
    print("[BOOT] watching:", path)
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
                        send_log(line, source)
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
    args = parser.parse_args()

    tail_file(args.path, args.source)

if __name__ == "__main__":
    main()
