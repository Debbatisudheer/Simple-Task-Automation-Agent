# chat_agent.py
import os

from openai import OpenAI


def chat_reply(prompt):
    """
    Handles chat replies.
    If OPENAI_API_KEY is missing, return fallback message.
    """

    api_key = os.getenv("OPENAI_API_KEY")  # picks key only if available

    if not api_key:
        return "⚠️ OpenAI API key is disabled by sudheer debbati. Chat features are currently unavailable."

    client = OpenAI(api_key=api_key)

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    return resp.choices[0].message.content
