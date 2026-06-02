import requests

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"


def call(api_key: str, messages: list, timeout: int = 60) -> str:
    """Call DeepSeek API and return the content string, or empty string on failure."""
    try:
        resp = requests.post(
            DEEPSEEK_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": "deepseek-chat", "messages": messages},
            timeout=timeout,
        )
        data = resp.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        return ""
    except Exception:
        return ""
