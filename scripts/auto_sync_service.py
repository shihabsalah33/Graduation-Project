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

import json

def verify_project_identity():
    sync_id_file = os.path.join(PROJECT_DIR, ".project_sync_id")
    if not os.path.exists(sync_id_file):
        return False
    try:
        with open(sync_id_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("project_id") == "shihabsalah33-graduation-project-sync-v1"
    except Exception:
        return False

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

import json

def get_git_branches():
    success, stdout, _ = run_git_command(["branch", "-a"])
    if not success:
        return []
    branches = []
    for line in stdout.splitlines():
        name = line.replace("*", "").strip()
        if "->" not in name:
            branches.append(name)
    return list(set(branches))

def get_git_history():
    fmt = "%H|%an|%ar|%s"
    success, stdout, _ = run_git_command(["log", "-n", "30", f"--pretty=format:{fmt}"])
    if not success:
        return []
    
    history = []
    for line in stdout.splitlines():
        parts = line.split("|")
        if len(parts) >= 4:
            chash = parts[0]
            success_diff, diff_text, _ = run_git_command(["show", "--stat", "--patch", chash])
            history.append({
                "commit": chash,
                "author": parts[1],
                "date": parts[2],
                "message": parts[3],
                "diff": diff_text if (success_diff and diff_text) else "لا توجد تغييرات نصية للمراجعة"
            })
    return history

def export_git_timeline():
    timeline_file = os.path.join(PROJECT_DIR, "chats", "git_timeline.json")
    data = {
        "branches": get_git_branches(),
        "history": get_git_history(),
        "current_head": run_git_command(["rev-parse", "HEAD"])[1]
    }
    try:
        with open(timeline_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"Export timeline error: {e}")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from open_ide_diff import check_and_execute_ide_diff
from chat_tracker_engine import sync_chat_tracker, verify_project_identity

from manual_sync_controller import check_and_execute_manual_triggers

def sync_repository():
    # Verify project identity first before doing anything
    if not verify_project_identity():
        log("Project identity verification failed. Skipping sync.")
        return

    # Check and execute manual push/pull triggers from HTML buttons
    try:
        check_and_execute_manual_triggers()
    except Exception:
        pass

    # Check for HTML Diff requests and trigger native IDE diff window
    try:
        check_and_execute_ide_diff()
    except Exception:
        pass

    # 1. Run deterministic chat tracker engine to auto-log messages
    try:
        sync_chat_tracker()
    except Exception as e:
        log(f"Chat tracker engine error: {e}")

    # 2. Always Auto-Pull remote changes first if online
    online = is_online()
    if online:
        run_git_command(["pull", "--rebase", "origin", "main"])

    # 2. Export updated Git timeline graph for UI
    export_git_timeline()

    # 3. Check for local changes
    success, stdout, stderr = run_git_command(["status", "--porcelain"])
    if not success or not stdout:
        return

    log("Pending local changes detected. Saving locally...")

    # 4. Stage all local changes
    success, _, stderr = run_git_command(["add", "-A"])
    if not success:
        log(f"Git add failed: {stderr}")
        return

    # 5. Commit changes locally
    commit_msg = f"Auto Sync: Local update [{datetime.now().strftime('%Y-%m-%d %H:%M')}]"
    success, _, stderr = run_git_command(["commit", "-m", commit_msg])
    if not success:
        return

    log("Local commit saved successfully.")
    export_git_timeline()

    # 6. Push to GitHub if online
    if online:
        log("Internet connection available. Syncing with GitHub...")
        run_git_command(["pull", "--rebase", "origin", "main"])
        success, stdout, stderr = run_git_command(["push", "origin", "main"])
        if success:
            log("Synced and Pushed to GitHub successfully!")
        else:
            log(f"Push deferred (will retry next cycle): {stderr}")
    else:
        log("Working Offline. Changes are saved locally and queued for auto-push when online.")

def sync_repository(on_exit=False):
    if not verify_project_identity():
        return

    # Check for manual push/pull button triggers
    try:
        check_and_execute_manual_triggers()
    except Exception:
        pass

    # Record latest chat messages locally
    try:
        sync_chat_tracker()
    except Exception:
        pass

    export_git_timeline()

    # Automatic Push ONLY occurs on session exit/closing if changes exist
    if on_exit:
        log("Session Exit / Close detected. Performing final automatic commit & push to GitHub...")
        run_git_command(["add", "-A"])
        commit_msg = f"Auto Sync On Exit [{datetime.now().strftime('%Y-%m-%d %H:%M')}]"
        run_git_command(["commit", "-m", commit_msg])
        if is_online():
            run_git_command(["pull", "--rebase", "origin", "main"])
            run_git_command(["push", "origin", "main"])
            log("Final exit push completed successfully!")

def main():
    log("Graduation Project Control Service Started.")
    import atexit
    atexit.register(lambda: sync_repository(on_exit=True))

    while True:
        try:
            sync_repository(on_exit=False)
        except Exception:
            pass
        time.sleep(3)

if __name__ == "__main__":
    main()
