# app.py — N3 Tag Server (auto-register via GitHub Gist)
from flask import Flask, request, jsonify
from datetime import datetime
import json
import os
import requests

app = Flask(__name__)

# ============ НАСТРОЙКИ ============
GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN", "")
GIST_ID       = os.environ.get("GIST_ID", "")
OWNER_USER_ID = 586169648
ONLINE_TIMEOUT = 120
# ===================================

GIST_API = f"https://api.github.com/gists/{GIST_ID}"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}

def load_users():
    if not GITHUB_TOKEN or not GIST_ID:
        return {}
    try:
        r = requests.get(GIST_API, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return {}
        data = r.json()
        content = data["files"]["users.json"]["content"]
        return json.loads(content) if content else {}
    except Exception as e:
        print(f"[load_users] error: {e}")
        return {}

def save_users(users):
    if not GITHUB_TOKEN or not GIST_ID:
        return False
    try:
        r = requests.patch(
            GIST_API,
            headers=HEADERS,
            json={"files": {"users.json": {"content": json.dumps(users, indent=2, ensure_ascii=False)}}},
            timeout=10,
        )
        return r.status_code == 200
    except Exception as e:
        print(f"[save_users] error: {e}")
        return False

def cleanup_offline(users):
    now = datetime.utcnow()
    cleaned = {}
    for uid, info in users.items():
        last = info.get("lastSeen", "")
        try:
            last_dt = datetime.fromisoformat(last)
            if (now - last_dt).total_seconds() < ONLINE_TIMEOUT:
                cleaned[uid] = info
        except Exception:
            pass
    return cleaned

@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "N3 tag server running", "brand": "N3mogg"})

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    uid = data.get("userId")
    if not uid:
        return jsonify({"ok": False, "reason": "no userId"}), 400

    uid = str(int(uid))
    users = load_users()

    users[uid] = {
        "userId":      int(uid),
        "displayName": str(data.get("displayName", ""))[:64],
        "name":        str(data.get("name", ""))[:64],
        "jobId":       str(data.get("jobId", "")),
        "placeId":     int(data.get("placeId", 0)),
        "executor":    str(data.get("executor", "Unknown"))[:64],
        "lastSeen":    datetime.utcnow().isoformat(),
        "firstSeen":   users.get(uid, {}).get("firstSeen", datetime.utcnow().isoformat()),
    }
    save_users(users)
    return jsonify({"ok": True})

@app.route("/users", methods=["GET"])
def users():
    users = load_users()
    cleaned = cleanup_offline(users)
    if cleaned != users:
        save_users(cleaned)
    return jsonify(list(cleaned.values()))

@app.route("/all", methods=["GET"])
def all_users():
    users = load_users()
    return jsonify(list(users.values()))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
