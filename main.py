# ============================================================
# main.py  (TEXT-ONLY JARVIS - NO VOICE)
# ============================================================

import os
from intent_agent import interpret, extract_email_and_message
from email_agent import send_email
from reminder_agent import set_reminder_with_email as set_reminder
from file_agent import organize_files
from chat_agent import chat_reply


HELP = """
✅ You can type commands like:

📧 Emails:
  send email to someone@example.com Hello how are you
  send happy birthday to someone@example.com

⏰ Reminders:
  remind me to drink water at 9am
  remind me at 23:20 to stretch
  remind me to pray at 7pm email me
  remind me to send report at 9am to my mail someone@example.com

🗂 File Organizer:
  organize files in "C:\\Users\\YourName\\Downloads"
  organize files in "C:\\Users\\YourName\\Downloads" dry run

💬 Chat:
  what is software
  who are you
  tell me about AI

Type **exit** to quit.
"""


def dispatch_one(intent: str, slots: dict):
    """Perform task based on extracted slots"""
    print(f"\n➡️ Debug: Intent={intent}, Slots={slots}")

    # --------------------------------------------------------
    # ✅ CHAT MODE (fallback message when API key disabled)
    # --------------------------------------------------------
    if intent == "chat":
        query = slots.get("query") or "introduce yourself"
        reply = chat_reply(query)

        if "disabled by admin" in reply.lower():
            print("⚠️ OpenAI API key is disabled by admin. Chat features unavailable.")
        else:
            print(f"🧠 Jarvis: {reply}")
        return

    # --------------------------------------------------------
    # ✅ SEND EMAIL
    # --------------------------------------------------------
    if intent == "send_email":
        to = slots.get("to")
        subject = slots.get("subject") or "Automated Email"
        msg = slots.get("message")

        # Missing email → ask user
        if not to:
            print("🟡 Who should I send it to?")
            reply = input("📥 Email: ")
            to, _ = extract_email_and_message(reply)

        # Missing message → ask user
        if not msg:
            print("🟡 What should be the message?")
            msg = input("📥 Message: ")

        if not (to and msg):
            print("❌ Missing email address or message.")
            return

        send_email(to, subject, msg)
        print(f"✅ Email sent to: {to}")
        return

    # --------------------------------------------------------
    # ✅ REMINDER
    # --------------------------------------------------------
    if intent == "set_reminder":
        time_str = slots.get("time")
        message = slots.get("message")
        email_to = slots.get("email_to")  # extracted if user says “to my email someone@example.com”

        # If user said "email me", fallback to env
        if not email_to and slots.get("email_me"):
            email_to = os.getenv("GMAIL_EMAIL")

        if not (time_str and message):
            print("❌ Missing reminder time or message.")
            return

        set_reminder(time_str, message, email_to)

        if email_to:
            print(f"⏰ Reminder set for {time_str} (Email will be sent to {email_to})")
        else:
            print(f"⏰ Reminder set for {time_str}")
        return

    # --------------------------------------------------------
    # ✅ FILE ORGANIZER
    # --------------------------------------------------------
    if intent == "organize_files":
        path = slots.get("path")
        dry = bool(slots.get("dry_run"))

        if not path:
            print("❌ Folder path missing.")
            return

        organize_files(path, dry_run=dry)
        print("✅ Files organized!" if not dry else "🔍 Dry run completed.")
        return

    # --------------------------------------------------------
    # ❓ UNKNOWN
    # --------------------------------------------------------
    print("❓ Unknown command. Type `help` to see what I can do.")
    print(HELP)


# ============================================================
# ✅ MAIN LOOP (NO DUPLICATION)
# ============================================================

if __name__ == "__main__":
    print("\n🤖 Jarvis Text Assistant Ready.")
    print("Type `help` to see commands. Type `exit` to quit.\n")

    while True:
        user = input("\n🧑 You: ").strip()

        if user.lower() in ["exit", "quit", "stop"]:
            print("👋 Bye! Have a great day.")
            break

        if user.lower() == "help":
            print(HELP)
            continue

        actions = interpret(user)
        for a in actions or []:
            dispatch_one(a.get("intent"), a.get("slots", {}))
