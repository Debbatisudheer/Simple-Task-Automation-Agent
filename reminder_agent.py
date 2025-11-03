from email_agent import send_email
import schedule
import time
import threading

_scheduler_started = False

def _run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

def _ensure_scheduler():
    """Runs scheduler in background if not already started"""
    global _scheduler_started
    if not _scheduler_started:
        threading.Thread(target=_run_scheduler, daemon=True).start()
        _scheduler_started = True

def set_reminder_with_email(time_str: str, message: str, email=None):
    """Schedules a reminder. 
    time_str: HH:MM format
    message: reminder text
    email: if provided, sends email reminder too
    """
    _ensure_scheduler()

    def task():
        print(f"🔔 Reminder: {message}")
        if email:
            send_email(email, "Reminder from AI Agent", message)

    schedule.every().day.at(time_str).do(task)
    print(f"⏳ Reminder set for {time_str}: {message}")
