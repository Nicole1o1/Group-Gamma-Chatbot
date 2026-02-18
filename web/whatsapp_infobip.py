"""Infobip WhatsApp helper utilities."""

from __future__ import annotations

import os
from typing import Any

import requests


def _normalize_base_url(base_url: str) -> str:
    base = base_url.strip()
    if not base:
        return ""
    if base.startswith("http://") or base.startswith("https://"):
        return base.rstrip("/")
    return f"https://{base.rstrip('/')}"


def load_whatsapp_config() -> dict[str, str]:
    """Load WhatsApp integration settings from environment variables."""
    return {
        "base_url": _normalize_base_url(os.getenv("INFOBIP_BASE_URL", "")),
        "api_key": os.getenv("INFOBIP_API_KEY", "").strip(),
        "sender": os.getenv("INFOBIP_WHATSAPP_SENDER", "").strip(),
    }


def is_whatsapp_configured() -> bool:
    cfg = load_whatsapp_config()
    return bool(cfg["base_url"] and cfg["api_key"] and cfg["sender"])


def send_whatsapp_text(to_number: str, text: str) -> tuple[int, dict[str, Any]]:
    """
    Send an outbound WhatsApp text message using Infobip.

    Returns: (status_code, response_json_or_error)
    """
    cfg = load_whatsapp_config()
    if not cfg["base_url"] or not cfg["api_key"] or not cfg["sender"]:
        return 500, {"error": "WhatsApp integration is not configured."}

    endpoint = f"{cfg['base_url']}/whatsapp/1/message/text"
    headers = {
        "Authorization": f"App {cfg['api_key']}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "from": cfg["sender"],
        "to": to_number,
        "content": {"text": text},
    }

    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        data = response.json() if response.content else {}
        return response.status_code, data
    except requests.RequestException as exc:
        return 502, {"error": f"Failed to call Infobip API: {exc}"}
    except ValueError:
        return response.status_code, {"raw": response.text}


def extract_inbound_text_messages(payload: dict[str, Any]) -> list[dict[str, str]]:
    """
    Parse Infobip inbound webhook payload and return text messages.

    Output rows: {"from": "<phone>", "text": "<message>"}
    """
    messages: list[dict[str, str]] = []
    results = payload.get("results")
    if not isinstance(results, list):
        return messages

    for item in results:
        if not isinstance(item, dict):
            continue
        from_number = str(item.get("from", "")).strip()
        message = item.get("message", {})
        text = ""
        if isinstance(message, dict):
            text = str(message.get("text", "")).strip()
        if not text:
            text = str(item.get("text", "")).strip()
        if from_number and text:
            messages.append({"from": from_number, "text": text})
    return messages
