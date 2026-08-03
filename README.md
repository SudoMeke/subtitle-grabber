# subtitle-grabber

[![Tests](https://github.com/SudoMeke/subtitle-grabber/actions/workflows/tests.yml/badge.svg)](https://github.com/SudoMeke/subtitle-grabber/actions/workflows/tests.yml)

Download YouTube subtitles from a full-screen terminal interface — no browser extensions, no video download, no ads. Works on Windows, macOS, and Linux.

Paste a YouTube link, pick a subtitle language from the list it shows you, choose where to save it (or accept the suggested default), and get a `.srt` file there.

## Requirements

- [Python 3](https://www.python.org/downloads/) (version 3.8 or newer).

That's it — no `ffmpeg`, no extra system tools. This tool only downloads subtitle files, not video, so it doesn't need anything beyond Python itself.

## Setup

1. **Download this project.** Either:
   - Click the green "Code" button on this repository's GitHub page → "Download ZIP", then extract it, **or**
   - If you have `git` installed: `git clone https://github.com/SudoMeke/subtitle-grabber`
2. **Open a terminal** in the extracted/cloned folder:
   - **Windows**: open the folder in File Explorer, then type `cmd` in the address bar and press Enter.
   - **macOS**: right-click the folder → "New Terminal at Folder" (or open Terminal and `cd` into it).
   - **Linux**: open a terminal and `cd` into the folder.
3. **Install it.** Two options:

   - **Recommended: [pipx](https://pipx.pypa.io/).** It installs the program in its own isolated environment while still giving you a `subgrabber` command usable from any folder — and it avoids the "externally-managed-environment" error that plain `pip` now throws on many Linux distros (Debian, Ubuntu, Fedora, Arch...).
     ```
     pipx install .
     ```
     If you don't have `pipx` yet: `python3 -m pip install --user pipx` (or on Arch: `sudo pacman -S python-pipx`, on macOS with Homebrew: `brew install pipx`), then `pipx ensurepath` and restart your terminal.

   - **Alternative: plain pip** (works out of the box on Windows and macOS with the official Python installer):
     ```
     pip install .
     ```
     (You may need `pip3` instead of `pip`.) If this fails with an "externally-managed-environment" error, use the `pipx` method above instead.

   Either way, this installs `yt-dlp` automatically and adds a `subgrabber` command you can run from any folder.

## Usage

```
subgrabber
```

A full-screen interface opens in your terminal. Type the YouTube URL and press Enter, pick a subtitle language from the list shown (or press Enter to accept the suggested one), choose a destination folder (or press Enter for the default, `Downloads/subtitles`), and it downloads.

Press `Esc` or `Ctrl+C` at any point to quit. The window needs to be at least 60 columns by 14 lines — if your terminal is smaller, resize it and try again.

## Running the tests

```
python -m unittest discover -s tests
```
(On macOS/Linux you may need `python3` instead of `python`.)

## License

MIT — see [LICENSE](LICENSE).
