import os
import sys
import json
import subprocess
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from chat_tracker_engine import sync_chat_tracker, verify_project_identity

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

IS_BUSY = False

def get_git_history():
    fmt = "%H|%an|%ar|%s"
    success, stdout, _ = run_git_command(["log", "-n", "15", f"--pretty=format:{fmt}"])
    if not success:
        return []
    
    history = []
    for line in stdout.splitlines():
        parts = line.split("|")
        if len(parts) >= 4:
            chash = parts[0]
            success_diff, diff_text, _ = run_git_command(["show", "--stat", "--patch", chash])
            clean_diff = diff_text[:4000] if (success_diff and diff_text) else "لا توجد تغييرات نصية للمراجعة"
            history.append({
                "commit": chash,
                "author": parts[1],
                "date": parts[2],
                "message": parts[3],
                "diff": clean_diff
            })
    return history

LAST_SYNC_STATUS = {
    "last_push_time": "لم يتم الرفع بعد",
    "last_push_status": "جاهز",
    "last_pull_time": "لم يتم الجلب بعد",
    "last_pull_status": "جاهز"
}

def export_git_timeline():
    timeline_file = os.path.join(PROJECT_DIR, "chats", "git_timeline.json")
    data = {
        "branches": get_git_branches(),
        "history": get_git_history(),
        "current_head": run_git_command(["rev-parse", "HEAD"])[1],
        "sync_status": LAST_SYNC_STATUS
    }
    try:
        with open(timeline_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def manual_push():
    global IS_BUSY
    if IS_BUSY:
        return False, "⏳ هناك عملية مزامنة جارية بالفعل، الرجاء الانتظار..."
    
    if not verify_project_identity():
        return False, "Project identity verification failed"

    IS_BUSY = True
    try:
        sync_chat_tracker()
        run_git_command(["add", "-A"])
        commit_msg = f"Manual Sync Push [{datetime.now().strftime('%Y-%m-%d %H:%M')}]"
        run_git_command(["commit", "-m", commit_msg])
        run_git_command(["pull", "--rebase", "origin", "main"])
        success, stdout, stderr = run_git_command(["push", "origin", "main"])
        
        # Clean workspace badges by committing timeline JSON update
        LAST_SYNC_STATUS["last_push_time"] = datetime.now().strftime("%H:%M:%S")
        LAST_SYNC_STATUS["last_push_status"] = "✅ تم الرفع بنجاح" if success else f"❌ فشل الرفع: {stderr[:30]}"
        export_git_timeline()

        if success:
            run_git_command(["add", "-A"])
            run_git_command(["commit", "-m", "Clean workspace badges"])
            run_git_command(["push", "origin", "main"])

        return success, stderr if not success else "Synced & Pushed successfully"
    finally:
        IS_BUSY = False

def manual_pull():
    global IS_BUSY
    if IS_BUSY:
        return False, "⏳ هناك عملية مزامنة جارية بالفعل، الرجاء الانتظار..."

    if not verify_project_identity():
        return False, "Project identity verification failed"

    IS_BUSY = True
    try:
        run_git_command(["add", "-A"])
        run_git_command(["commit", "-m", f"Auto save before pull [{datetime.now().strftime('%H:%M:%S')}]"])
        success, stdout, stderr = run_git_command(["pull", "--rebase", "origin", "main"])
        sync_chat_tracker()
        
        LAST_SYNC_STATUS["last_pull_time"] = datetime.now().strftime("%H:%M:%S")
        LAST_SYNC_STATUS["last_pull_status"] = "✅ تم الجلب بنجاح" if success else f"❌ فشل الجلب: {stderr[:30]}"
        export_git_timeline()
        return success, stderr if not success else "Pulled successfully"
    finally:
        IS_BUSY = False

def check_and_execute_manual_triggers():
    trigger_push_file = os.path.join(PROJECT_DIR, "chats", ".trigger_push")
    trigger_pull_file = os.path.join(PROJECT_DIR, "chats", ".trigger_pull")

    if os.path.exists(trigger_push_file):
        manual_push()
        try:
            os.remove(trigger_push_file)
        except Exception:
            pass

    if os.path.exists(trigger_pull_file):
        manual_pull()
        try:
            os.remove(trigger_pull_file)
        except Exception:
            pass

def main():
    while True:
        try:
            check_and_execute_manual_triggers()
        except Exception:
            pass
        import time
        time.sleep(2)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "push":
            ok, msg = manual_push()
            print(msg)
        elif action == "pull":
            ok, msg = manual_pull()
            print(msg)
    else:
        main()
