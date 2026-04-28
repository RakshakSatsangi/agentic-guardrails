#!/usr/bin/env python3
"""
Cursor beforeSubmitPrompt hook: block prompts containing email addresses.
Asks for confirmation via the email-guard-hook VS Code extension (HTTP on port 37123).
"""

import json
import re
import sys
import urllib.request

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE)
EXTENSION_URL = "http://127.0.0.1:37123"


def respond(data: dict):
    sys.stdout.write(json.dumps(data) + "\n")
    sys.stdout.flush()


def ask_via_cursor(emails: list) -> bool:
    email_list = ", ".join(emails[:5])
    message = f"Email address(es) detected: {email_list} — proceed with this prompt?"
    payload = json.dumps({"message": message}).encode()

    req = urllib.request.Request(
        EXTENSION_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            return bool(result.get("proceed", False))
    except Exception:
        return False


def main():
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        respond({"continue": True})
        return

    prompt = ""
    for key in ("prompt", "message", "userPrompt", "text"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            prompt = val
            break

    emails = list(dict.fromkeys(EMAIL_RE.findall(prompt)))

    if not emails:
        respond({"continue": True})
        return

    proceed = ask_via_cursor(emails)

    if proceed:
        respond({"continue": True})
    else:
        respond({
            "continue": False,
            "user_message": f"Blocked: email address(es) detected ({', '.join(emails[:5])}).",
        })


if __name__ == "__main__":
    try:
        main()
    except Exception:
        respond({"continue": True})
