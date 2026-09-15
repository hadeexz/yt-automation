"""
Send a phone push through ntfy.sh when a Short posts or a job fails.

Free Android/iOS app: https://ntfy.sh
Set NTFY_TOPIC in .env and as a GitHub Actions secret.
"""

from __future__ import annotations

import os
import urllib.error
import urllib.request

from src.youtube_auth import USER_AGENT

NTFY_BASE = os.environ.get("NTFY_SERVER", "https://ntfy.sh")


def _post(
    title: str,
    message: str,
    click: str = "",
    tags: str = "",
    priority: str = "default",
) -> bool:
    topic = (os.environ.get("NTFY_TOPIC") or "").strip()
    if not topic:
        print("No NTFY_TOPIC set, skipping phone notify")
        return False

    headers = {
        "User-Agent": USER_AGENT,
        "Title": title[:250],
        "Priority": priority,
    }
    if click:
        headers["Click"] = click
        headers["Actions"] = f"view, Open, {click}"
    if tags:
        headers["Tags"] = tags

    req = urllib.request.Request(
        f"{NTFY_BASE.rstrip('/')}/{topic}",
        data=message.encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            print(f"Phone notify sent ({resp.status})")
            return True
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:200]
        print(f"Phone notify failed: {exc.code} {body}")
        return False
    except Exception as exc:
        print(f"Phone notify failed: {exc}")
        return False


def notify_posted(title: str, video_id: str, duration: float, window: str) -> bool:
    url = f"https://www.youtube.com/watch?v={video_id}" if video_id else ""
    seconds = int(round(float(duration or 0)))
    return _post(
        title="How Come? posted",
        message=f"{title}\n{window} slot · {seconds}s\n{url}".strip(),
        click=url,
        tags="movie_camera,white_check_mark",
        priority="high",
    )


def notify_failed(window: str = "") -> bool:
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    run_url = f"{server}/{repo}/actions/runs/{run_id}" if repo and run_id else ""
    slot = window or os.environ.get("POST_SLOT") or "daily"
    return _post(
        title="How Come? post failed",
        message=f"The {slot} Short did not upload.\n{run_url}".strip(),
        click=run_url,
        tags="warning",
        priority="high",
    )
