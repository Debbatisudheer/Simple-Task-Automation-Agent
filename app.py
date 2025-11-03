import streamlit as st
from intent_agent import interpret, extract_email_and_message
from email_agent import send_email
from reminder_agent import set_reminder_with_email
from file_agent import organize_files
from chat_agent import chat_reply
import os

# Streamlit Config
st.set_page_config(page_title="Jarvis AI Assistant", page_icon="🤖", layout="centered")

st.title("🤖 Jarvis Automation Agent")
st.write("Type a command and Jarvis will execute it.\nExamples:")
st.code("""
send happy birthday to someone@gmail.com
remind me to drink water at 10:30
organize files in C:\\Users\\Downloads
what is software engineering?
""")

# Chat history initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

def add_to_chat(role, content):
    st.session_state.messages.append({"role": role, "content": content})

def dispatch(intent, slots):
    """Mapping intents → actions"""

    if intent == "send_email":
        to = slots.get("to")
        subject = slots.get("subject") or "Automated Email"
        msg = slots.get("message")

        # Slot filling (if missing message or email)
        if not to:
            return "❌ Missing email address."

        if not msg:
            msg = "Happy Birthday!"  # default if not spoken

        send_email(to, subject, msg)
        return f"✅ Email sent to **{to}**."

    elif intent == "set_reminder":
        time_str = slots.get("time")
        message = slots.get("message") or "Reminder"

        email_to = slots.get("email_to") or os.getenv("GMAIL_EMAIL")

        set_reminder_with_email(time_str, message, email_to)
        return f"⏰ Reminder set for **{time_str}**."

    elif intent == "organize_files":
        path = slots.get("path")
        dry = bool(slots.get("dry_run"))

        if not path:
            return "⚠️ Missing folder path."

        organize_files(path, dry_run=dry)
        return "✅ Files organized." if not dry else "✅ Dry run completed."

    else:
        query = slots.get("query") or "Tell me something."
        return chat_reply(query)

# Chat input
prompt = st.chat_input("Ask Jarvis anything...")

if prompt:
    add_to_chat("user", prompt)
    actions = interpret(prompt)

    for action in actions:
        response = dispatch(action["intent"], action["slots"])
        add_to_chat("assistant", response)

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
