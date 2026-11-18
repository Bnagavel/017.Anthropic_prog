"""
discord_gate.py — Mobile notification & confirmation gate via Discord REST API.

Environment Variables (or .env in 010.AutoHex_loop/):
  DISCORD_BOT_TOKEN   : Bot token (required for two-way mobile reply polling)
  DISCORD_CHANNEL_ID  : Channel ID where cards are posted and replies are read
  DISCORD_WEBHOOK_URL : Optional webhook URL (one-way fallback if no bot token)

Supported Mobile Replies (case-insensitive):
  PROCEED             -> Approve plan and trigger code execution
  REFINE: <feedback>  -> Re-run Gemini spec generation with your feedback
  SKIP                -> Mark current model skipped and move to next
"""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


DISCORD_API_BASE = "https://discord.com/api/v10"
USER_AGENT = "DiscordBot (https://discord.com, 10)"


def _get_bot_invite_url(bot_token: Optional[str]) -> Optional[str]:
    """Extract client_id from the first segment of the Discord bot token and build an invite URL."""
    if not bot_token or "." not in bot_token:
        return None
    try:
        first_part = bot_token.split(".")[0]
        padding = "=" * (-len(first_part) % 4)
        client_id = base64.b64decode(first_part + padding).decode("utf-8").strip()
        if client_id.isdigit():
            # Permissions 68608 = View Channels (1024) + Send Messages (2048) + Read Message History (65536) + Embed Links (16384 -> 84992)
            return f"https://discord.com/oauth2/authorize?client_id={client_id}&permissions=84992&scope=bot"
    except Exception:
        pass
    return None


def load_env_file(env_path: Optional[Path] = None) -> None:
    """Load simple KEY=VALUE pairs from .env if present."""
    path = env_path or (Path(__file__).resolve().parent / ".env")
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _discord_request(
    method: str,
    url: str,
    bot_token: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Any:
    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
    }
    if bot_token:
        headers["Authorization"] = f"Bot {bot_token}"

    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        err_body = ""
        try:
            err_body = exc.read().decode("utf-8")
        except Exception:
            pass
        print(f"\n[DISCORD ERROR] HTTP {exc.code} ({exc.reason}): {err_body}")
        if exc.code == 403:
            invite_url = _get_bot_invite_url(bot_token)
            _diagnose_missing_access(bot_token, invite_url)
        raise


def _diagnose_missing_access(bot_token: Optional[str], invite_url: Optional[str]) -> None:
    """Check which servers/channels the bot can actually see and print exact fix instructions."""
    if not bot_token:
        return
    try:
        headers = {"User-Agent": USER_AGENT, "Authorization": f"Bot {bot_token}"}
        req = urllib.request.Request(f"{DISCORD_API_BASE}/users/@me/guilds", headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            guilds = json.loads(resp.read().decode("utf-8"))
    except Exception:
        guilds = None

    if not guilds:
        print("\n[DIAGNOSIS] Your bot is currently in 0 Discord servers!")
        if invite_url:
            print("-> Open this URL in your browser to add the bot to your server:")
            print(f"   {invite_url}")
        return

    print("\n[DIAGNOSIS] Your bot IS in the following server(s), checking visible text channels:")
    for g in guilds:
        gid = g.get("id")
        gname = g.get("name")
        print(f"  Server: {gname} (Server ID: {gid})")
        try:
            req = urllib.request.Request(f"{DISCORD_API_BASE}/guilds/{gid}/channels", headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                channels = json.loads(resp.read().decode("utf-8"))
            text_channels = [c for c in channels if c.get("type") == 0]
            for c in text_channels:
                print(f"    -> #{c.get('name')}  |  DISCORD_CHANNEL_ID={c.get('id')}")
        except Exception as e:
            print(f"    (Could not list channels: {e})")
    print("\n-> Make sure DISCORD_CHANNEL_ID in .env matches one of the channel IDs above,")
    print("   and if the channel has a lock icon (Private), add the Bot in Edit Channel -> Permissions!")


def _get_discord_creds() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    load_env_file()
    bot_token = (os.environ.get("DISCORD_BOT_TOKEN") or "").strip()
    channel_id = (os.environ.get("DISCORD_CHANNEL_ID") or "").strip()
    webhook_url = (os.environ.get("DISCORD_WEBHOOK_URL") or "").strip()

    if bot_token in ("", "your_discord_bot_token_here"):
        bot_token = None
    if channel_id in ("", "your_discord_channel_id_here"):
        channel_id = None
    if not webhook_url:
        webhook_url = None
    return bot_token, channel_id, webhook_url


def send_status_embed(
    title: str,
    model_rel_path: str,
    status: str,
    metrics: Dict[str, Any],
    gemini_spec_summary: str,
    color: int = 0xE67E22,
) -> Optional[str]:
    """Post a rich status embed to Discord and return the sent message ID."""
    bot_token, channel_id, webhook_url = _get_discord_creds()

    metrics_str = (
        f"**Valid:** `{metrics.get('valid', False)}` | "
        f"**Winner:** `{metrics.get('strategy', 'none')}`\n"
        f"**Hex Count:** `{metrics.get('n_hex', 0)}` | "
        f"**Coverage:** `{metrics.get('coverage_pct', 0.0):.1f}%`\n"
        f"**minSJ:** `{metrics.get('min_sj', 0.0):.3f}` | "
        f"**maxAR:** `{metrics.get('max_ar', 0.0):.2f}` | "
        f"**Inversions:** `{metrics.get('inversions', 0)}`"
    )

    spec_preview = gemini_spec_summary.strip()
    if len(spec_preview) > 950:
        spec_preview = spec_preview[:947] + "..."

    embed = {
        "title": title[:250],
        "color": color,
        "fields": [
            {"name": "Model", "value": f"`{model_rel_path}`"[:1024], "inline": True},
            {"name": "Status", "value": f"`{status}`"[:1024], "inline": True},
            {"name": "Baseline Metrics", "value": metrics_str[:1024], "inline": False},
            {
                "name": "Gemini Proposed Spec",
                "value": (spec_preview or "_No spec details_")[:1024],
                "inline": False,
            },
            {
                "name": "Reply on Mobile",
                "value": "`PROCEED`  |  `NEXT`  |  `SKIP`  |  `STATUS`",
                "inline": False,
            },
        ],
    }

    payload = {"embeds": [embed]}

    if bot_token and channel_id:
        url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
        resp = _discord_request("POST", url, bot_token=bot_token, payload=payload)
        return str(resp.get("id")) if resp else None

    if webhook_url:
        _discord_request("POST", webhook_url, payload=payload)
        return None

    # Console fallback when Discord credentials are not configured yet
    print("\n" + "=" * 70)
    print(f"[DISCORD PREVIEW] {title}")
    print(f"Model  : {model_rel_path} ({status})")
    print(f"Metrics: {metrics}")
    print("-" * 70)
    print(spec_preview)
    print("=" * 70)
    return None


def wait_for_decision(
    after_message_id: Optional[str] = None,
    poll_interval_sec: int = 10,
    timeout_sec: int = 14400,
) -> Tuple[str, str]:
    """Wait for user reply ('PROCEED', 'REFINE', or 'SKIP') via Discord or CLI fallback.

    Returns:
        (action, feedback) where action is one of: "PROCEED", "REFINE", "SKIP"
    """
    bot_token, channel_id, _ = _get_discord_creds()

    if not (bot_token and channel_id):
        print("\n[LOCAL GATE] Discord Bot Token/Channel not set. Enter decision locally:")
        while True:
            raw = input("Type PROCEED, REFINE: <note>, or SKIP > ").strip()
            parsed = _parse_reply(raw)
            if parsed:
                return parsed

    print(f"[DISCORD GATE] Waiting for mobile reply in channel {channel_id}...")
    start_ts = time.time()
    last_seen_id = after_message_id

    while (time.time() - start_ts) < timeout_sec:
        try:
            query = "?limit=10"
            if last_seen_id:
                query += f"&after={urllib.parse.quote(str(last_seen_id))}"
            url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages{query}"
            messages = _discord_request("GET", url, bot_token=bot_token)

            if isinstance(messages, list) and messages:
                # Discord returns newest first; iterate oldest-to-newest
                for msg in reversed(messages):
                    msg_id = str(msg.get("id", ""))
                    if msg_id:
                        last_seen_id = msg_id
                    if msg.get("author", {}).get("bot"):
                        continue
                    content = (msg.get("content") or "").strip()
                    parsed = _parse_reply(content)
                    if parsed:
                        return parsed
        except urllib.error.URLError as exc:
            print(f"[DISCORD GATE] Network warning: {exc}; retrying...")

        time.sleep(poll_interval_sec)

    raise TimeoutError("Timed out waiting for Discord mobile confirmation.")


def send_file_message(file_path: Path, caption: str = "") -> Optional[str]:
    """Upload an image/file attachment with an optional caption to Discord via multipart/form-data."""
    bot_token, channel_id, webhook_url = _get_discord_creds()
    if not file_path.exists():
        return send_text_message(f"⚠️ Image file not found: `{file_path}`\n{caption}")

    boundary = f"----AutoHexBoundary{int(time.time() * 1000)}"
    crlf = b"\r\n"
    body_parts = []

    payload_json = json.dumps({"content": caption[:1900]}).encode("utf-8")
    body_parts.append(f"--{boundary}".encode("utf-8"))
    body_parts.append(b'Content-Disposition: form-data; name="payload_json"')
    body_parts.append(b"Content-Type: application/json")
    body_parts.append(b"")
    body_parts.append(payload_json)

    file_bytes = file_path.read_bytes()
    body_parts.append(f"--{boundary}".encode("utf-8"))
    body_parts.append(
        f'Content-Disposition: form-data; name="files[0]"; filename="{file_path.name}"'.encode("utf-8")
    )
    body_parts.append(b"Content-Type: image/png")
    body_parts.append(b"")
    body_parts.append(file_bytes)
    body_parts.append(f"--{boundary}--".encode("utf-8"))
    body_parts.append(b"")

    raw_body = crlf.join(body_parts)
    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }

    target_url = None
    if bot_token and channel_id:
        target_url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
        headers["Authorization"] = f"Bot {bot_token}"
    elif webhook_url:
        target_url = webhook_url

    if not target_url:
        print(f"\n[DISCORD FILE] {file_path} — {caption}\n")
        return None

    req = urllib.request.Request(target_url, data=raw_body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp_body = resp.read().decode("utf-8")
            data = json.loads(resp_body) if resp_body else {}
            return str(data.get("id")) if data.get("id") else None
    except urllib.error.HTTPError as exc:
        print(f"[DISCORD FILE] Direct attachment returned HTTP {exc.code}; falling back to inline Embed image...")
        img_url = _upload_temp_image(file_path)
        if img_url and bot_token and channel_id:
            embed_payload = {
                "content": caption[:1900],
                "embeds": [{"title": file_path.name, "image": {"url": img_url}, "color": 0x2ECC71}],
            }
            url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
            resp = _discord_request("POST", url, bot_token=bot_token, payload=embed_payload)
            return str(resp.get("id")) if resp else None
        return send_text_message(f"{caption}\n_(Image saved locally at `{file_path}`)_")


def _upload_temp_image(file_path: Path) -> Optional[str]:
    """Upload PNG to 1-hour temporary Litterbox host so Discord can render it inside an Embed."""
    boundary = f"----LitterBoundary{int(time.time() * 1000)}"
    crlf = b"\r\n"
    parts = []
    for name, val in (("reqtype", "fileupload"), ("time", "1h")):
        parts.append(f"--{boundary}".encode("utf-8"))
        parts.append(f'Content-Disposition: form-data; name="{name}"'.encode("utf-8"))
        parts.append(b"")
        parts.append(val.encode("utf-8"))

    parts.append(f"--{boundary}".encode("utf-8"))
    parts.append(
        f'Content-Disposition: form-data; name="fileToUpload"; filename="{file_path.name}"'.encode("utf-8")
    )
    parts.append(b"Content-Type: image/png")
    parts.append(b"")
    parts.append(file_path.read_bytes())
    parts.append(f"--{boundary}--".encode("utf-8"))
    parts.append(b"")

    body = crlf.join(parts)
    req = urllib.request.Request(
        "https://litterbox.catbox.moe/resources/internals/api.php",
        data=body,
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            url = resp.read().decode("utf-8").strip()
            if url.startswith("https://"):
                return url
    except Exception as exc:
        print(f"[TEMP IMAGE HOST] Warning: {exc}")
    return None


def send_text_message(content: str) -> Optional[str]:
    """Post a plain markdown message to Discord (chunked if >1900 chars) and return the last message ID."""
    bot_token, channel_id, webhook_url = _get_discord_creds()
    text = content.strip() or "_(Empty response)_"
    chunks = [text[i : i + 1900] for i in range(0, len(text), 1900)]
    last_id: Optional[str] = None

    for chunk in chunks:
        payload = {"content": chunk}
        if bot_token and channel_id:
            url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
            resp = _discord_request("POST", url, bot_token=bot_token, payload=payload)
            if resp and resp.get("id"):
                last_id = str(resp["id"])
        elif webhook_url:
            _discord_request("POST", webhook_url, payload=payload)
        else:
            print(f"\n[DISCORD CHAT]\n{chunk}\n")
    return last_id


def get_latest_message_id() -> Optional[str]:
    """Fetch the ID of the most recent message in the channel so we only listen to new messages."""
    bot_token, channel_id, _ = _get_discord_creds()
    if not (bot_token and channel_id):
        return None
    try:
        url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages?limit=1"
        messages = _discord_request("GET", url, bot_token=bot_token)
        if isinstance(messages, list) and messages:
            return str(messages[0].get("id", ""))
    except Exception:
        pass
    return None


def wait_for_next_user_message(
    after_message_id: Optional[str] = None,
    poll_interval_sec: int = 5,
    timeout_sec: int = 86400,
) -> Tuple[str, Optional[str]]:
    """Wait for ANY next message from the user on Discord (for continuous chat mode).

    Returns:
        (message_text, message_id)
    """
    bot_token, channel_id, _ = _get_discord_creds()
    if not (bot_token and channel_id):
        raw = input("\n[CHAT > ] ").strip()
        return raw, None

    start_ts = time.time()
    last_seen_id = after_message_id or get_latest_message_id()

    while (time.time() - start_ts) < timeout_sec:
        try:
            query = "?limit=10"
            if last_seen_id:
                query += f"&after={urllib.parse.quote(str(last_seen_id))}"
            url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages{query}"
            messages = _discord_request("GET", url, bot_token=bot_token)

            if isinstance(messages, list) and messages:
                for msg in reversed(messages):
                    msg_id = str(msg.get("id", ""))
                    if msg_id:
                        last_seen_id = msg_id
                    if msg.get("author", {}).get("bot"):
                        continue
                    content = (msg.get("content") or "").strip()
                    if content:
                        return content, last_seen_id
        except urllib.error.URLError as exc:
            print(f"[DISCORD GATE] Network warning: {exc}; retrying...")

        time.sleep(poll_interval_sec)

    raise TimeoutError("Timed out waiting for Discord message.")


def _parse_reply(text: str) -> Optional[Tuple[str, str]]:
    """Parse user message into ('PROCEED'|'REFINE'|'SKIP', feedback)."""
    upper = text.strip().upper()
    if upper == "PROCEED":
        return ("PROCEED", "")
    if upper == "SKIP":
        return ("SKIP", "")
    if upper.startswith("REFINE"):
        parts = text.split(":", 1)
        feedback = parts[1].strip() if len(parts) > 1 else text[6:].strip()
        return ("REFINE", feedback)
    return None

