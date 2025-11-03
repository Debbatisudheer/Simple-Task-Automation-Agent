# memory_agent.py
import json
import os

MEMORY_FILE = "memory.json"


def init_memory():
    if not os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "w") as f:
            json.dump({}, f)


def save_memory(key: str, value: str):
    data = load_all_memory()
    data[key.lower()] = value

    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

    print("💾 Saved memory:", data)


def load_all_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}

    with open(MEMORY_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def get_memory(key: str):
    data = load_all_memory()
    return data.get(key.lower())


