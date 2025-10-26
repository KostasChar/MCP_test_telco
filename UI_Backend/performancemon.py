import requests
import re
import time
import psutil
import csv
import os
from collections import defaultdict
from datetime import datetime
import pytz

URL = "http://localhost:9009/debug/objgraph"
INTERVAL = 5  # seconds between polls
LOG_FILE = "memory_monitor_log_greece.csv"

# List of interesting, memory-related objects
INTERESTING = [
    "MemoryObjectSendStream",
    "MemoryObjectStreamState",
    "Event",
    "_AsyncGeneratorContextManager",
    "_GeneratorContextManager",
    "TaskState"
]

# Data storage
counts = defaultdict(list)

# Prepare CSV log file
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode="w", newline="") as f:
        writer = csv.writer(f)
        header = ["timestamp_greece", "rss_MB"] + INTERESTING
        writer.writerow(header)


def parse_objgraph_output(text):
    """Extract object names and total counts from objgraph output"""
    pattern = r"(\w+)\s+(\d+)\s+\+\d+"
    return {name: int(total) for name, total in re.findall(pattern, text)}


process = psutil.Process()
tz_greece = pytz.timezone("Europe/Athens")

print(f"📊 Starting Greece-time memory monitor — logging to {LOG_FILE}")
print(f"Polling {URL} every {INTERVAL} seconds...\nPress Ctrl+C to stop.\n")

while True:
    try:
        # Request data from Quart debug endpoint
        resp = requests.get(URL, timeout=5)
        resp.raise_for_status()
        data = parse_objgraph_output(resp.text)

        # Greece-local timestamp
        timestamp_greece = datetime.now(tz_greece).strftime("%Y-%m-%d %H:%M:%S")

        rss = process.memory_info().rss / (1024 * 1024)  # MB

        # Prepare row with counts for interesting objects
        row = [timestamp_greece, rss]
        for name in INTERESTING:
            value = data.get(name, counts[name][-1] if counts[name] else 0)
            counts[name].append(value)
            row.append(value)

        # Append to CSV
        with open(LOG_FILE, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(row)

        time.sleep(INTERVAL)

    except KeyboardInterrupt:
        print(f"\n🛑 Stopping monitor. Data saved to {LOG_FILE}")
        break
    except Exception as e:
        print(f"⚠️ Error: {e}")
        time.sleep(INTERVAL)


