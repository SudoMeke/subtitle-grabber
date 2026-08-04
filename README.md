# subtitle-grabber

[![Tests](https://github.com/SudoMeke/subtitle-grabber/actions/workflows/tests.yml/badge.svg)](https://github.com/SudoMeke/subtitle-grabber/actions/workflows/tests.yml)

Download YouTube subtitles from a full-screen terminal interface — no browser extensions, no video download, no ads. Works on Windows, macOS, and Linux.

Paste a YouTube link, pick a subtitle language from the list it shows you, choose where to save it (or accept the suggested default), and get a `.srt` file there.

## Install (no Python needed)

Go to the [Releases page](https://github.com/SudoMeke/subtitle-grabber/releases/latest) and download the file for your system:

- **Windows**: `subgrabber-windows.exe` — double-click it (or run it from `cmd`/PowerShell).
- **macOS**: `subgrabber-macos` — since it isn't signed by an Apple-registered developer, the first time you'll need to right-click it → "Open" → "Open" again to get past Gatekeeper's warning (only needed once).
- **Linux**: `subgrabber-linux` — make it executable first: `chmod +x subgrabber-linux`, then run it with `./subgrabber-linux`.

That's it — nothing else to install. Skip to [Usage](#usage) below.

## Alternative: install from source (requires Python)

Useful if you want to read/modify the code, or if you'd rather have a `subgrabber` command on your PATH instead of a standalone file.

- [Python 3](https://www.python.org/downloads/) (version 3.8 or newer).

No `ffmpeg` or other system tools needed either way — this tool only downloads subtitle files, not video.

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

Run the file you downloaded (`subgrabber-windows.exe`, `./subgrabber-macos`, or `./subgrabber-linux`), or just `subgrabber` if you installed it with pipx/pip.

A full-screen interface opens in your terminal. Type the YouTube URL and press Enter, pick a subtitle language from the list shown (or press Enter to accept the suggested one), choose a destination folder (or press Enter for the default, `Downloads/subtitles`), and it downloads.

Press `Esc` or `Ctrl+C` at any point to quit. The window needs to be at least 60 columns by 14 lines — if your terminal is smaller, resize it and try again.

## Running the tests

```
python -m unittest discover -s tests
```
(On macOS/Linux you may need `python3` instead of `python`.)

## License

MIT — see [LICENSE](LICENSE).
