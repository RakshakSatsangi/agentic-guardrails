#!/usr/bin/env python3
"""
Cursor beforeSubmitPrompt hook: block prompts containing email addresses,
but ask the user first via a native macOS dialog.
"""

import json
import re
import subprocess
import sys

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE)


def extract_prompt(payload: dict) -> str:
    for key in ("prompt", "message", "userPrompt", "text"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return json.dumps(payload, ensure_ascii=False)


def ask_user(emails: list, preview: str) -> bool:
    email_list = "\\n".join(f"• {e}" for e in emails[:5])
    short_preview = preview[:200].replace('"', '\\"').replace("'", "\\'")

    script = f"""
        set msg to "Email address(es) detected in prompt:\\n\\n{email_list}\\n\\nPrompt preview:\\n{short_preview}\\n\\nProceed anyway?"
        set chosen to button returned of (display dialog msg ¬
            buttons {{"Block", "Proceed"}} ¬
            default button "Block" ¬
            with title "Cursor Hook - Email Detected" ¬
            with icon caution)
        return chosen
    """

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=60
        )
        return result.returncode == 0 and result.stdout.strip() == "Proceed"
    except Exception:
        return False


def main():
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        print(json.dumps({"decision": "allow"}))
        return

    prompt = extract_prompt(payload)
    emails = list(dict.fromkeys(EMAIL_RE.findall(prompt)))  # deduplicated, ordered

    if not emails:
        out = json.dumps({"continue": True})
        sys.stdout.write(out + "\n")
        sys.stdout.flush()
        return

    proceed = ask_user(emails, prompt)

    if proceed:
        out = json.dumps({"continue": True})
    else:
        out = json.dumps({
            "continue": False,
            "user_message": f"Blocked: prompt contained email address(es): {', '.join(emails[:5])}.",
        })

    sys.stdout.write(out + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stdout.write(json.dumps({"continue": True}) + "\n")
        sys.stdout.flush()
