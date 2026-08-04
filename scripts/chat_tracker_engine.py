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

import re

def clean_user_message(raw_text):
    if not raw_text:
        return ""
    # Extract only text inside <USER_REQUEST>...</USER_REQUEST> if present
    match = re.search(r'<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>', raw_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Remove system metadata tags if present
    clean_text = re.sub(r'<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>', '', raw_text, flags=re.DOTALL)
    clean_text = re.sub(r'<USER_SETTINGS_CHANGE>.*?</USER_SETTINGS_CHANGE>', '', clean_text, flags=re.DOTALL)
    clean_text = re.sub(r'<USER_REQUEST>', '', clean_text)
    clean_text = re.sub(r'</USER_REQUEST>', '', clean_text)
    return clean_text.strip()

def clean_ai_message(raw_text):
    if not raw_text:
        return ""
    # Remove markdown bold/italic asterisks, hash headers, and raw file links
    text = re.sub(r'[\*\#\`\~]', '', raw_text)
    text = re.sub(r'\(file:\/\/\/.*?\)', '', text)
    text = re.sub(r'\[(.*?)\]', r'\1', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def extract_project_messages():
    if not verify_project_identity():
        return []

    log_files = find_app_data_brain_logs()
    if not log_files:
        return []

    # Parse and merge transcript logs sorted by file modification time
    log_files.sort(key=os.path.getmtime)
    latest_file = log_files[-1]
    
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
                        cleaned = clean_user_message(content)
                        if cleaned:
                            if current_user_msg:
                                messages.append({
                                    "id": len(messages) + 1,
                                    "sender": user_name,
                                    "userMessage": current_user_msg,
                                    "aiMessage": clean_ai_message(current_ai_msg) if current_ai_msg else "جاري المعالجة..."
                                })
                                current_ai_msg = ""
                            current_user_msg = cleaned
                    
                    elif entry_type == "PLANNER_RESPONSE" and content:
                        current_ai_msg += content + "\n"
                except Exception:
                    continue

            if current_user_msg:
                messages.append({
                    "id": len(messages) + 1,
                    "sender": user_name,
                    "userMessage": current_user_msg,
                    "aiMessage": clean_ai_message(current_ai_msg) if current_ai_msg else "جاري المعالجة..."
                })
    except Exception:
        pass

    return messages

def sync_chat_tracker():
    new_messages = extract_project_messages()
    if not new_messages:
        return

    # Clean existing user messages from XML tags if present
    for msg in new_messages:
        msg["userMessage"] = clean_user_message(msg.get("userMessage", ""))

    try:
        with open(CHAT_JSON, "w", encoding="utf-8") as f:
            json.dump(new_messages, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

if __name__ == "__main__":
    sync_chat_tracker()
