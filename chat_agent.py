# chat_agent.py
from openai import OpenAI

client = OpenAI()

def chat_reply(query: str) -> str:
    """Returns conversational response using GPT."""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Reply like Jarvis. Short and smart."},
            {"role": "user", "content": query}
        ]
    )
    return resp.choices[0].message.content
