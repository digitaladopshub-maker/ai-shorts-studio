"""Shared yt-dlp downloader configuration for supported social platforms."""

import os
import shutil
import subprocess
import sys


def get_deno_runtime():
    """Return an explicit Deno executable path, or None if unavailable."""
    try:
        import deno
        runtime = deno.find_deno_bin()
        if runtime and os.path.isfile(runtime):
            return runtime
    except Exception:
        pass
    return shutil.which("deno")


def build_ytdlp_command(url, output_path, deno_runtime, fallback=False):
    """Build a yt-dlp command using Deno + the bundled yt-dlp-ejs scripts."""
    command = [
        sys.executable, "-m", "yt_dlp",
        "--no-check-certificates",
        "--geo-bypass",
        "--js-runtimes", f"deno:{deno_runtime}",
        "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--output", output_path,
    ]
    if fallback:
        command.extend(["--extractor-args", "youtube:player_client=web_safari"])
    command.append(url)
    return command


def download_video_from_url(url, output_path, deno_runtime, fallback=False):
    """Run yt-dlp and return its completed process result."""
    if fallback and os.path.exists(output_path):
        os.remove(output_path)
    return subprocess.run(
        build_ytdlp_command(url, output_path, deno_runtime, fallback),
        capture_output=True,
        text=True,
    )
