# subtitle-grabber

Download YouTube subtitles from the terminal — no browser extensions, no video download, no ads. Works on Windows, macOS, and Linux.

Paste a YouTube link, pick a subtitle language from the list it shows you, and get a `.srt` file in a `subtitles` folder next to the program.

## Requirements

- [Python 3](https://www.python.org/downloads/) (version 3.8 or newer).

That's it — no `ffmpeg`, no extra system tools. This tool only downloads subtitle files, not video, so it doesn't need anything beyond Python itself.

## Setup

1. **Download this project.** Either:
   - Click the green "Code" button on this repository's GitHub page → "Download ZIP", then extract it, **or**
   - If you have `git` installed: `git clone <this-repo-url>`
2. **Open a terminal** in the extracted/cloned folder:
   - **Windows**: open the folder in File Explorer, then type `cmd` in the address bar and press Enter.
   - **macOS**: right-click the folder → "New Terminal at Folder" (or open Terminal and `cd` into it).
   - **Linux**: open a terminal and `cd` into the folder.
3. **Install the one dependency:**
   ```
   pip install -r requirements.txt
   ```
   (On macOS/Linux you may need `pip3` instead of `pip`.)

## Usage

```
python subtitle_grabber.py
```
(On macOS/Linux you may need `python3` instead of `python`.)

Then follow the prompts:

```
YouTube URL: https://www.youtube.com/watch?v=...
Looking up available subtitles...

"Some Video Title"
Available subtitles:
  en - English (official)
  es - Spanish (auto-generated)

Language code to download [en]:
Downloading...
Saved to: subtitles/Some Video Title.en.srt
```

Press Enter at the language prompt to accept the suggested (first-listed) language, or type any code shown in the list.

## License

MIT — see [LICENSE](LICENSE).
