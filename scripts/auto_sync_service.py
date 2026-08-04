import os
import sys
import time
import subprocess
from datetime import datetime

# Root Directory of Graduation Project
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(PROJECT_DIR, "chats", ".sync_service.log")

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] {message}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted_msg)
    except Exception:
        pass

def run_git_command(args):
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def is_online():
    # Quick check if internet/remote is reachable
    success, _, _ = run_git_command(["ls-remote", "origin", "-h", "refs/heads/main"])
    return success

def sync_repository():
    # 1. Always Auto-Pull remote changes first if online
    online = is_online()
    if online:
        # Pull latest changes without overriding unstaged local files
        run_git_command(["pull", "--rebase", "origin", "main"])

    # 2. Check for local changes (chats, json, html, code, etc.)
    success, stdout, stderr = run_git_command(["status", "--porcelain"])
    if not success or not stdout:
        return

    log("Pending local changes detected. Saving locally...")

    # 3. Stage all local changes (Offline or Online)
    success, _, stderr = run_git_command(["add", "-A"])
    if not success:
        log(f"Git add failed: {stderr}")
        return

    # 4. Commit changes locally
    commit_msg = f"Auto Sync: Local update [{datetime.now().strftime('%Y-%m-%d %H:%M')}]"
    success, _, stderr = run_git_command(["commit", "-m", commit_msg])
    if not success:
        return

    log("Local commit saved successfully.")

    # 5. Push to GitHub if online
    if online:
        log("Internet connection available. Syncing with GitHub...")
        # Pull rebase once more before pushing to solve non-fast-forward silently
        run_git_command(["pull", "--rebase", "origin", "main"])
        success, stdout, stderr = run_git_command(["push", "origin", "main"])
        if success:
            log("Synced and Pushed to GitHub successfully!")
        else:
            log(f"Push deferred (will retry next cycle): {stderr}")
    else:
        log("Working Offline. Changes are saved locally and queued for auto-push when online.")

def main():
    log("Graduation Project Auto-Sync Service Started.")
    check_interval = 20  # check every 20 seconds

    while True:
        try:
            sync_repository()
        except Exception as e:
            log(f"Unexpected service error: {str(e)}")
        
        time.sleep(check_interval)

if __name__ == "__main__":
    main()
