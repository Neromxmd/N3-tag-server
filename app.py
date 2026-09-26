# app.py — N3 Tag Server
from flask import Flask, request, jsonify
from datetime import datetime
import json
import os

app = Flask(__name__)

# ============ НАСТРОЙКИ ============
TAG_FILE = "tags.json"
# Список UserId, которым разрешено видеть теги (ты и твои друзья)
ALLOWED_USERS = {
    586169648: "N3mogg",   # ← ЗАМЕНИ НА СВОЙ UserId
    # 1234567890: "Друг1",
    # 9876543210: "Друг2",
}
# ===================================

def load_tags():
    if not os.path.exists(TAG_FILE):
        return {}
    with open(TAG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_tags(data):
    with open(TAG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    uid = data.get("userId")
    if not uid:
        return jsonify({"ok": False, "reason": "no userId"}), 400

    uid = int(uid)
    if uid not in ALLOWED_USERS:
        return jsonify({"ok": False, "reason": "not allowed"}), 403

    tags = load_tags()
    tags[str(uid)] = {
        "userId":      uid,
        "displayName": data.get("displayName", ""),
        "name":        data.get("name", ""),
        "jobId":       data.get("jobId", ""),
        "placeId":     data.get("placeId", 0),
        "executor":    data.get("executor", "Unknown"),
        "lastSeen":    datetime.utcnow().isoformat(),
    }
    save_tags(tags)
    return jsonify({"ok": True})

@app.route("/users", methods=["GET"])
def users():
    tags = load_tags()
    now = datetime.utcnow()
    cleaned = {}
    for k, v in tags.items():
        try:
            last = datetime.fromisoformat(v.get("lastSeen", ""))
            if (now - last).total_seconds() < 120:
                cleaned[k] = v
        except Exception:
            pass
    if cleaned != tags:
        save_tags(cleaned)
    return jsonify(list(cleaned.values()))

@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "N3 tag server running", "brand": "N3"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
