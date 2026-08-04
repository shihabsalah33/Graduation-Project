import os
import json
import subprocess

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMAND_TRIGGER_FILE = os.path.join(PROJECT_DIR, "chats", ".diff_request.json")

def check_and_execute_ide_diff():
    if not os.path.exists(COMMAND_TRIGGER_FILE):
        return

    try:
        with open(COMMAND_TRIGGER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        commit_hash = data.get("commit_hash")
        if commit_hash:
            # Trigger native VS Code / Antigravity diff window command
            cmd = f'code --diff HEAD "{commit_hash}"'
            subprocess.run(["git", "difftool", "-y", f"{commit_hash}^!", "--"], cwd=PROJECT_DIR, creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            
        os.remove(COMMAND_TRIGGER_FILE)
    except Exception:
        pass

if __name__ == "__main__":
    check_and_execute_ide_diff()
