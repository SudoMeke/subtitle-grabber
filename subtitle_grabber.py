#!/usr/bin/env python3
"""Download YouTube subtitles from the terminal on Windows, macOS, or Linux.

No account, no browser, no video download: paste a YouTube URL, pick a
subtitle language, and get a .srt file in the "subtitles" folder next to
this script.
"""

import sys
from pathlib import Path

import yt_dlp

SUBS_DIR = Path.cwd() / "subtitles"


def is_youtube_url(url):
    return "youtube.com" in url or "youtu.be" in url


def _is_real_caption(fmt):
    """Automatic captions include auto-translations into ~170 languages;
    those have tlang= in their URL. Skip them so the language list only
    shows genuine transcripts."""
    return "tlang=" not in fmt.get("url", "")


def get_subtitle_options(url):
    """Return {"title": str, "languages": {code: {"name": str, "auto": bool}}}."""
    ydl_opts = {"skip_download": True, "quiet": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    languages = {}
    for code, formats in (info.get("subtitles") or {}).items():
        languages[code] = {"name": formats[0].get("name", code), "auto": False}
    for code, formats in (info.get("automatic_captions") or {}).items():
        if code in languages:
            continue
        real_formats = [f for f in formats if _is_real_caption(f)]
        if real_formats:
            languages[code] = {"name": real_formats[0].get("name", code), "auto": True}

    return {"title": info.get("title", "Unknown title"), "languages": languages}


def download_subtitle(url, lang_code, auto, out_dir=SUBS_DIR):
    """Download one subtitle track as .srt and return the written file's path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    ydl_opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "writesubtitles": not auto,
        "writeautomaticsubtitles": auto,
        "subtitleslangs": [lang_code],
        "subtitlesformat": "srt",
        "outtmpl": str(out_dir / "%(title)s.%(ext)s"),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    matches = sorted(out_dir.glob(f"*.{lang_code}.srt"), key=lambda p: p.stat().st_mtime)
    return matches[-1] if matches else None


def friendly_error(error_text):
    text = error_text.lower()
    if "private video" in text:
        return "That video is private."
    if "video unavailable" in text:
        return "That video is unavailable (deleted or region-blocked)."
    if "sign in" in text or "confirm your age" in text:
        return "That video requires sign-in and can't be downloaded here."
    return "Couldn't read that video. Double-check the URL and try again."


def prompt_and_download():
    url = input("YouTube URL: ").strip()
    if not is_youtube_url(url):
        print("That doesn't look like a YouTube URL.")
        return None

    print("Looking up available subtitles...")
    try:
        info = get_subtitle_options(url)
    except yt_dlp.utils.DownloadError as exc:
        print(friendly_error(str(exc)))
        return None

    if not info["languages"]:
        print(f'"{info["title"]}" has no subtitles available.')
        return None

    print(f'\n"{info["title"]}"')
    print("Available subtitles:")
    codes = sorted(info["languages"])
    for code in codes:
        details = info["languages"][code]
        kind = "auto-generated" if details["auto"] else "official"
        print(f"  {code} - {details['name']} ({kind})")

    default_code = codes[0]
    choice = input(f"\nLanguage code to download [{default_code}]: ").strip() or default_code
    if choice not in info["languages"]:
        print(f"'{choice}' isn't in the list above.")
        return None

    print("Downloading...")
    try:
        path = download_subtitle(url, choice, info["languages"][choice]["auto"])
    except yt_dlp.utils.DownloadError as exc:
        print(friendly_error(str(exc)))
        return None

    if path is None:
        print("Download finished, but the file couldn't be found afterwards.")
        return None

    print(f"Saved to: {path}")
    return path


def run():
    try:
        prompt_and_download()
    except KeyboardInterrupt:
        print("\nCancelled.")


if __name__ == "__main__":
    sys.exit(run())
