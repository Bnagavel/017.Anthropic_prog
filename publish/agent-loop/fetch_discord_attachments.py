"""Fetch recent Discord user messages and download any image attachments into logs/."""
from pathlib import Path
import json
import urllib.request
from discord_gate import DISCORD_API_BASE, USER_AGENT, _discord_request, _get_discord_creds

LOOP_DIR = Path(__file__).resolve().parent
LOGS_DIR = LOOP_DIR / "logs"

def main():
    bot_token, channel_id, _ = _get_discord_creds()
    if not (bot_token and channel_id):
        print("No Discord credentials")
        return
    url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages?limit=10"
    messages = _discord_request("GET", url, bot_token=bot_token)
    downloaded = []
    for msg in reversed(messages):
        if msg.get("author", {}).get("bot"):
            continue
        msg_id = msg.get("id")
        content = msg.get("content", "")
        attachments = msg.get("attachments", [])
        print(f"MSG {msg_id}: {content!r} | attachments={len(attachments)}")
        for idx, att in enumerate(attachments):
            att_url = att.get("url")
            fn = att.get("filename", f"att_{idx}.png")
            ext = Path(fn).suffix or ".png"
            out_path = LOGS_DIR / f"user_sketch_{msg_id}_{idx}{ext}"
            req = urllib.request.Request(att_url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=20) as resp:
                out_path.write_bytes(resp.read())
            print(f"  -> Downloaded attachment to {out_path}")
            downloaded.append(str(out_path))
    (LOGS_DIR / "latest_user_attachments.json").write_text(json.dumps(downloaded, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
