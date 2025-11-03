import re
import json
import os

# ================================================================
# Helpers
# ================================================================

def normalize_spoken_email(text: str) -> str | None:
    if not text:
        return None
    t = text.lower().strip()
    replacements = {
        " at the rate ": "@",
        " at ": "@",
        " underscore ": "_",
        " under score ": "_",
        " dot ": ".",
        " dash ": "-",
        " hyphen ": "-",
        " space ": "",
    }
    for spoken, symbol in replacements.items():
        t = t.replace(spoken, symbol)
    t = re.sub(r"\s*@\s*", "@", t)
    t = re.sub(r"\s*\.\s*", ".", t)
    return t


def extract_email_and_message(text: str):
    if not text:
        return None, None
    text_norm = normalize_spoken_email(text)
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text_norm or "")
    email = email_match.group(0) if email_match else None
    msg = (text_norm or "").replace(email, "", 1).strip() if email else None
    return email, msg


def _to_hhmm(hour: int, minute: int, ampm: str | None) -> str | None:
    # Convert hour/min + am/pm into 24h HH:MM
    if ampm:
        ampm = ampm.lower()
        if hour == 12:
            hour = 0 if ampm == "am" else 12
        elif ampm == "pm":
            hour += 12
    if 0 <= hour <= 23 and 0 <= minute <= 59:
        return f"{hour:02d}:{minute:02d}"
    return None


def parse_time_from_text(text: str) -> str | None:
    """
    Supports:
      23:19
      9 am / 9am
      9:05 pm / 9:05pm
      23:20am (messy but seen in speech)
    Returns HH:MM (24h) or None
    """
    t = text.lower().strip().replace(" ", "")
    # 1) H:MM(am|pm)? or HH:MM(am|pm)?
    m = re.search(r"\b(\d{1,2}):(\d{2})(am|pm)?\b", t)
    if m:
        hh = int(m.group(1)); mm = int(m.group(2)); ap = m.group(3)
        return _to_hhmm(hh, mm, ap)
    # 2) H(am|pm)
    m = re.search(r"\b(\d{1,2})(am|pm)\b", t)
    if m:
        hh = int(m.group(1)); ap = m.group(2)
        return _to_hhmm(hh, 0, ap)
    # 3) Bare HH:MM 24h
    m = re.search(r"\b(\d{1,2}):(\d{2})\b", t)
    if m:
        hh = int(m.group(1)); mm = int(m.group(2))
        return _to_hhmm(hh, mm, None)
    return None


# ================================================================
# RULE-BASED INTENT DETECTION
# ================================================================

def _rule_based_parse(text: str):
    original = text
    t = text.lower().strip()
    # strip wake words just in case
    t = t.replace("hey jarvis", "").replace("jarvis", "").strip()

    # ----- CHAT -----
    if any(q in t for q in ["what is", "who are you", "explain", "tell me", "define "]):
        return [{"intent": "chat", "slots": {"query": original}}]

    # ----- EMAIL: "send happy birthday to someone@example.com"
    m = re.match(r"send (?:a )?(?:happy birthday|birthday wish|birthday message) to (.+)", t)
    if m:
        email_or_name = m.group(1).strip()
        email = normalize_spoken_email(email_or_name)
        return [{
            "intent": "send_email",
            "slots": {
                "to": email if (email and "@" in email) else None,
                "subject": "Happy Birthday!",
                "message": "Happy Birthday! 🎉"
            }
        }]

    # ----- EMAIL: "send email to someone@example.com <message>"
    m = re.match(r"send email to (\S+)\s+(.+)", t)
    if m:
        email = normalize_spoken_email(m.group(1))
        msg = m.group(2)
        return [{"intent": "send_email", "slots": {"to": email, "subject": "Automated Email", "message": msg}}]

    # ----- REMINDER patterns -----

    # A) "remind me to <message> at <time> [email me|to my mail <email>]"
    m = re.match(
        r"(?:remind me|set reminder)\s+(?:to\s+)?(.+?)\s+(?:at|@)\s+([^\s]+(?:\s?(?:am|pm))?)\s*(?:.*?(email me)|.*?(?:to|at)\s*(?:my\s*)?mail\s*(\S+))?$",
        t
    )
    if m:
        message = m.group(1).strip()
        timestr_raw = m.group(2).strip()
        email_me_flag = bool(m.group(3))
        email_raw = m.group(4)
        hhmm = parse_time_from_text(timestr_raw)
        email_to = normalize_spoken_email(email_raw) if email_raw else None
        return [{
            "intent": "set_reminder",
            "slots": {"time": hhmm, "message": message, "email_me": email_me_flag, "email_to": email_to}
        }]

    # B) "remind me at <time> to <message> [email me|to my mail <email>]"
    m = re.match(
        r"(?:remind me|set reminder)\s+(?:at|@)\s+([^\s]+(?:\s?(?:am|pm))?)\s+(?:to\s+)?(.+?)(?:\s*(email me)|\s*(?:to|at)\s*(?:my\s*)?mail\s*(\S+))?$",
        t
    )
    if m:
        timestr_raw = m.group(1).strip()
        message = m.group(2).strip()
        email_me_flag = bool(m.group(3))
        email_raw = m.group(4)
        hhmm = parse_time_from_text(timestr_raw)
        email_to = normalize_spoken_email(email_raw) if email_raw else None
        return [{
            "intent": "set_reminder",
            "slots": {"time": hhmm, "message": message, "email_me": email_me_flag, "email_to": email_to}
        }]

    return None


# ================================================================
# LLM FALLBACK
# ================================================================

def _llm_parse(text: str):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    system_prompt = """
You are an intent extractor for a CLI assistant.

Allowed intents:
  - send_email (slots: to, subject, message)
  - set_reminder (slots: time, message, email_me, email_to)
  - organize_files (slots: path, dry_run)
  - chat (slots: query)

If user says things like "remind me to drink water at 9am email me", set:
  "time": "09:00" (24h),
  "message": "drink water",
  "email_me": true

If they provide an email inside text, set "email_to".
Return ONLY valid JSON array.
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
        )
        raw = resp.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "")
        parsed = json.loads(raw)
        parsed = parsed if isinstance(parsed, list) else [parsed]

        # Post-fix: try to fill missing reminder slots using our parser
        for item in parsed:
            if item.get("intent") == "set_reminder":
                slots = item.setdefault("slots", {})
                # try to parse time if missing
                if not slots.get("time"):
                    slots["time"] = parse_time_from_text(text)
                # try to parse message if missing
                if not slots.get("message"):
                    # crude: strip the leading verb and time phrase
                    msg = re.sub(r"(remind me|set reminder)\s+(to\s+)?", "", text, flags=re.I)
                    msg = re.sub(r"\s+(at|@)\s+.*$", "", msg, flags=re.I).strip()
                    slots["message"] = msg or None
                # email flags
                if "email me" in text.lower() and not slots.get("email_me"):
                    slots["email_me"] = True
                if not slots.get("email_to"):
                    e,_ = extract_email_and_message(text)
                    slots["email_to"] = e

        return parsed

    except Exception as e:
        print("LLM parse failed:", e)
        return None


# ================================================================
# MAIN
# ================================================================

def interpret(text: str):
    parsed = _rule_based_parse(text)
    if parsed:
        print("⚡ Intent detected using RULE-BASED logic")
        return parsed

    llm_parsed = _llm_parse(text)
    if llm_parsed:
        print("🧠 Intent detected using LLM")
        return llm_parsed

    print("❓ Unknown → defaulting to CHAT")
    return [{"intent": "chat", "slots": {"query": text}}]
