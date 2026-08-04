import os
import glob
import json
import getpass
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYNC_ID_FILE = os.path.join(PROJECT_DIR, ".project_sync_id")
CHAT_JSON = os.path.join(PROJECT_DIR, "chats", "chat_history.json")

def get_current_user_name():
    # Detect current Windows/User username accurately
    try:
        user = getpass.getuser()
        if user.lower() in ["shihab", "shiha"]:
            return "Shihab (مالك المشروع)"
        elif "mostafa" in user.lower():
            return "Mostafa (عضو الفريق)"
        return f"{user} (عضو الفريق)"
    except Exception:
        return "عضو الفريق"

def verify_project_identity():
    if not os.path.exists(SYNC_ID_FILE):
        return False
    try:
        with open(SYNC_ID_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("project_id") == "shihabsalah33-graduation-project-sync-v1"
    except Exception:
        return False

def find_app_data_brain_logs():
    user_home = os.path.expanduser("~")
    brain_path = os.path.join(user_home, ".gemini", "antigravity-ide", "brain")
    if not os.path.exists(brain_path):
        return []
    
    # Search for transcript JSONL files in active brain logs
    logs = glob.glob(os.path.join(brain_path, "*", ".system_generated", "logs", "transcript.jsonl"))
    return logs

def extract_project_messages():
    if not verify_project_identity():
        return []

    log_files = find_app_data_brain_logs()
    if not log_files:
        return []

    # Get the latest modified conversation transcript file
    latest_file = max(log_files, key=os.path.getmtime)
    
    messages = []
    current_user_msg = ""
    current_ai_msg = ""
    user_name = get_current_user_name()

    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    entry_type = entry.get("type")
                    content = entry.get("content", "")

                    if entry_type == "USER_INPUT" and content:
                        if current_user_msg and current_ai_msg:
                            messages.append({
                                "id": len(messages) + 1,
                                "sender": user_name,
                                "userMessage": current_user_msg,
                                "aiMessage": current_ai_msg
                            })
                            current_ai_msg = ""
                        current_user_msg = content
                    
                    elif entry_type == "PLANNER_RESPONSE" and content:
                        current_ai_msg += content + "\n"
                except Exception:
                    continue

            if current_user_msg and current_ai_msg:
                messages.append({
                    "id": len(messages) + 1,
                    "sender": user_name,
                    "userMessage": current_user_msg,
                    "aiMessage": current_ai_msg
                })
    except Exception:
        pass

    return messages

def sync_chat_tracker():
    new_messages = extract_project_messages()
    if not new_messages:
        return

    # Check existing messages in project chat_history.json
    existing = []
    if os.path.exists(CHAT_JSON):
        try:
            with open(CHAT_JSON, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []

    # Update only if transcript extracted more items
    if len(new_messages) > len(existing):
        try:
            with open(CHAT_JSON, "w", encoding="utf-8") as f:
                json.dump(new_messages, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

if __name__ == "__main__":
    sync_chat_tracker()
