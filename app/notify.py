from __future__ import annotations

import requests


def _telegram_error_detail(response: requests.Response | None) -> str:
    if response is None:
        return "no response body"

    try:
        data = response.json()
    except ValueError:
        return "no JSON error description"

    description = data.get("description")
    if isinstance(description, str) and description:
        return description
    return "no Telegram description provided"


def send_telegram_message(bot_token: str, chat_id: str, text: str) -> bool:
    if not bot_token or not chat_id:
        print("Telegram is not configured; skipping notification.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    response = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        },
        timeout=20,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        detail = _telegram_error_detail(exc.response)
        raise requests.HTTPError(
            f"Telegram API error (status={status}): {detail}"
        ) from None
    return True


def send_telegram_test_message(
    bot_token: str,
    chat_id: str,
    text: str = "Developer Opportunity Monitor test notification",
) -> tuple[bool, str]:
    if not bot_token or not chat_id:
        return (
            False,
            "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing.",
        )

    try:
        send_telegram_message(bot_token, chat_id, text)
    except requests.RequestException as exc:
        return (False, f"Telegram rejected the message: {exc}")

    return (True, "Telegram accepted the test message.")


def diagnose_telegram(bot_token: str, chat_id: str) -> tuple[bool, list[str]]:
    notes: list[str] = []

    if not bot_token:
        notes.append("Missing TELEGRAM_BOT_TOKEN in .env")
    if not chat_id:
        notes.append("Missing TELEGRAM_CHAT_ID in .env")
    if notes:
        return False, notes

    base_url = f"https://api.telegram.org/bot{bot_token}"

    try:
        me_response = requests.get(f"{base_url}/getMe", timeout=20)
    except requests.RequestException as exc:
        return False, [
            f"Network/API request failed while calling getMe: {exc}"
        ]

    if me_response.status_code != 200:
        detail = _telegram_error_detail(me_response)
        return False, [
            f"Token check failed (getMe status={me_response.status_code}).",
            f"Telegram said: {detail}",
            "Verify TELEGRAM_BOT_TOKEN is correct.",
        ]

    me_data = me_response.json()
    if not me_data.get("ok"):
        detail = me_data.get("description") or "no description provided"
        return False, [
            "Token check failed (getMe returned ok=false).",
            f"Telegram said: {detail}",
            "Verify TELEGRAM_BOT_TOKEN is correct.",
        ]

    bot_username = (
        (me_data.get("result") or {}).get("username") or "<unknown>"
    )
    notes.append(f"Token is valid (bot username: @{bot_username}).")

    try:
        chat_response = requests.get(
            f"{base_url}/getChat", params={"chat_id": chat_id}, timeout=20
        )
    except requests.RequestException as exc:
        notes.append(
            f"Network/API request failed while calling getChat: {exc}"
        )
        return False, notes

    if chat_response.status_code == 200:
        chat_data = chat_response.json()
        if chat_data.get("ok"):
            chat = chat_data.get("result") or {}
            chat_type = chat.get("type", "unknown")
            title = chat.get("title") or chat.get("username") or "<no title>"
            notes.append(f"Chat ID is valid ({chat_type}: {title}).")
            notes.append("Bot should be able to send messages to this chat.")
            return True, notes

    notes.append(
        f"Chat check failed (getChat status={chat_response.status_code})."
    )
    notes.append(
        f"Telegram said: {_telegram_error_detail(chat_response)}"
    )
    notes.append("Ensure TELEGRAM_CHAT_ID is correct for the target chat.")
    notes.append("For direct messages, open chat with bot and send /start.")
    notes.append("For groups/channels, add bot and grant posting permission.")
    return False, notes


def list_candidate_chat_ids(bot_token: str) -> tuple[bool, list[str]]:
    if not bot_token:
        return False, ["Missing TELEGRAM_BOT_TOKEN in .env"]

    base_url = f"https://api.telegram.org/bot{bot_token}"

    try:
        response = requests.get(
            f"{base_url}/getUpdates",
            params={"limit": 100, "timeout": 0},
            timeout=20,
        )
    except requests.RequestException as exc:
        return False, [
            f"Network/API request failed while calling getUpdates: {exc}"
        ]

    if response.status_code != 200:
        detail = _telegram_error_detail(response)
        return False, [
            f"getUpdates failed (status={response.status_code}).",
            f"Telegram said: {detail}",
        ]

    payload = response.json()
    if not payload.get("ok"):
        detail = payload.get("description") or "no description provided"
        return False, [
            "getUpdates returned ok=false.",
            f"Telegram said: {detail}",
        ]

    updates = payload.get("result") or []
    if not updates:
        return False, [
            "No updates found.",
            (
                "Send /start to the bot (DM) or post in the "
                "target group/channel, then retry."
            ),
        ]

    seen: dict[str, str] = {}
    for update in updates:
        message_obj = (
            update.get("message")
            or update.get("channel_post")
            or update.get("edited_message")
            or update.get("edited_channel_post")
        )
        if not message_obj:
            continue

        chat = message_obj.get("chat") or {}
        chat_id = chat.get("id")
        if chat_id is None:
            continue

        chat_type = chat.get("type", "unknown")
        label = (
            chat.get("title")
            or chat.get("username")
            or chat.get("first_name")
            or "<unnamed>"
        )
        seen[str(chat_id)] = f"chat_id={chat_id} ({chat_type}: {label})"

    if not seen:
        return False, [
            "Updates were found but no chat IDs could be extracted.",
            (
                "Send /start to the bot or send a message in the "
                "target chat, then retry."
            ),
        ]

    lines = [
        "Candidate TELEGRAM_CHAT_ID values from recent updates:",
    ]
    lines.extend(sorted(seen.values()))
    return True, lines
