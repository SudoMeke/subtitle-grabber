"""Full-screen terminal interface for subtitle-grabber, built on curses."""

import curses
import curses.ascii
import curses.textpad
import textwrap
import threading
import unicodedata
from pathlib import Path

import subtitle_grabber

_SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧"
_MIN_LINES, _MIN_COLS = 14, 60
_BANNER_H, _STATUS_H, _INPUT_H, _HINT_H = 4, 1, 3, 1

_TITLE = "Ｓ Ｕ Ｂ Ｇ Ｒ Ａ Ｂ Ｂ Ｅ Ｒ"
_SUBTITLE = "» YouTube subtitles, in your terminal «"
_HINT = "[Enter] confirm    [Esc / Ctrl+C] quit"

_COLOR = {}


def _display_width(text):
    """Column width of text, counting East Asian wide/fullwidth chars as 2."""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


class _Quit(Exception):
    """Raised (and left uncaught until run()) to unwind out of curses on Esc/Ctrl+C."""


class _TooSmall(Exception):
    pass


class _Resized(Exception):
    """Raised inside ask()'s Textbox loop on KEY_RESIZE so the prompt can restart at the new size."""


def _init_colors():
    curses.start_color()
    bg = 234 if curses.COLORS >= 256 else curses.COLOR_BLACK
    curses.init_pair(1, curses.COLOR_CYAN, bg)
    curses.init_pair(2, curses.COLOR_MAGENTA, bg)
    curses.init_pair(3, curses.COLOR_GREEN, bg)
    curses.init_pair(4, curses.COLOR_YELLOW, bg)
    curses.init_pair(5, curses.COLOR_RED, bg)
    curses.init_pair(6, curses.COLOR_WHITE, bg)
    if curses.COLORS >= 256:
        curses.init_pair(7, 208, bg)  # vivid orange, distinct from cyan/magenta/green below
        title_attr = curses.color_pair(7) | curses.A_BOLD
    else:
        title_attr = curses.color_pair(4) | curses.A_BOLD  # fallback: basic yellow
    _COLOR.update(
        border=curses.color_pair(1) | curses.A_BOLD,
        accent=curses.color_pair(2) | curses.A_BOLD,
        ok=curses.color_pair(3) | curses.A_BOLD,
        warn=curses.color_pair(4) | curses.A_BOLD,
        err=curses.color_pair(5) | curses.A_BOLD,
        fg=curses.color_pair(6),
        title=title_attr,
    )


class _Screen:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.log_lines = []
        self.lines = self.cols = 0
        self._layout()

    def _layout(self):
        self.lines, self.cols = self.stdscr.getmaxyx()
        log_h = max(3, self.lines - _BANNER_H - _STATUS_H - _INPUT_H - _HINT_H)
        self.banner_win = self.stdscr.derwin(_BANNER_H, self.cols, 0, 0)
        self.status_win = self.stdscr.derwin(_STATUS_H, self.cols, _BANNER_H, 0)
        self.log_win = self.stdscr.derwin(log_h, self.cols, _BANNER_H + _STATUS_H, 0)
        self.input_win = self.stdscr.derwin(_INPUT_H, self.cols, self.lines - _INPUT_H - _HINT_H, 0)
        self.hint_win = self.stdscr.derwin(_HINT_H, self.cols, self.lines - _HINT_H, 0)
        for win in (self.banner_win, self.status_win, self.log_win, self.input_win, self.hint_win):
            win.bkgd(" ", _COLOR["fg"])
        self.redraw_chrome()

    def maybe_resize(self):
        if curses.is_term_resized(self.lines, self.cols):
            new_lines, new_cols = self.stdscr.getmaxyx()
            curses.resizeterm(new_lines, new_cols)
            self.stdscr.clear()
            self._layout()

    def _box(self, win, label=""):
        try:
            win.attron(_COLOR["border"])
            win.box()
            if label:
                win.addstr(0, 2, f" {label} ", _COLOR["accent"])
            win.attroff(_COLOR["border"])
        except curses.error:
            pass

    def redraw_chrome(self):
        win = self.banner_win
        win.erase()
        self._box(win)
        w = win.getmaxyx()[1]
        try:
            win.addstr(1, max(2, (w - _display_width(_TITLE)) // 2), _TITLE, _COLOR["title"])
            win.addstr(2, max(2, (w - len(_SUBTITLE)) // 2), _SUBTITLE, _COLOR["accent"])
        except curses.error:
            pass
        win.refresh()

        win = self.hint_win
        win.erase()
        try:
            win.addstr(0, max(0, (self.cols - len(_HINT)) // 2), _HINT[: self.cols - 1], _COLOR["accent"])
        except curses.error:
            pass
        win.refresh()

        self._draw_input_border("")
        self._redraw_log_lines()
        self._draw_status("")

    def _draw_status(self, text):
        win = self.status_win
        win.erase()
        if text:
            try:
                win.addstr(0, max(0, (self.cols - len(text)) // 2), text[: self.cols - 1], _COLOR["accent"])
            except curses.error:
                pass
        win.refresh()

    def _draw_input_border(self, prompt):
        win = self.input_win
        win.erase()
        self._box(win, "INPUT")
        if prompt:
            try:
                win.addstr(1, 2, prompt[: win.getmaxyx()[1] - 4], _COLOR["ok"])
            except curses.error:
                pass
        win.refresh()

    def _redraw_log_lines(self):
        win = self.log_win
        win.erase()
        self._box(win, "LOG")
        inner_h, inner_w = win.getmaxyx()[0] - 2, win.getmaxyx()[1] - 4
        for idx, (text, attr) in enumerate(self.log_lines[-inner_h:]):
            try:
                win.addstr(1 + idx, 2, text[:inner_w], attr)
            except curses.error:
                pass
        win.refresh()

    def log(self, text, style="fg"):
        attr = _COLOR.get(style, curses.A_NORMAL)
        inner_w = max(4, self.cols - 6)
        for line in text.splitlines() or [""]:
            for wrapped in textwrap.wrap(line, inner_w) or [""]:
                self.log_lines.append((wrapped, attr))
        self._redraw_log_lines()

    def ask(self, prompt):
        # A resize while blocked inside Textbox.edit() below can't be
        # relayouted in place (the field's window would need to be swapped
        # out from under a running edit loop) -- simplest correct fix is to
        # drop what was typed so far, relayout everything at the new size,
        # and restart the same prompt fresh.
        while True:
            self.maybe_resize()
            self._draw_input_border(prompt)
            win = self.input_win
            h, w = win.getmaxyx()
            field_col = min(w - 3, 3 + len(prompt))
            field_w = max(4, w - field_col - 2)
            field_win = win.derwin(1, field_w, 1, field_col)
            field_win.bkgd(" ", _COLOR["fg"])
            field_win.erase()
            field_win.keypad(True)
            try:
                curses.curs_set(1)
            except curses.error:
                pass

            def validate(ch):
                if ch in (curses.ascii.ETX, curses.ascii.ESC):
                    raise _Quit
                if ch == curses.KEY_RESIZE:
                    raise _Resized
                if ch in (curses.ascii.CR, curses.ascii.NL):
                    return curses.ascii.BEL
                if ch in (127, curses.KEY_BACKSPACE):
                    return curses.ascii.BS
                return ch

            box = curses.textpad.Textbox(field_win, insert_mode=True)
            try:
                text = box.edit(validate).strip()
            except _Resized:
                curses.flushinp()
                continue
            finally:
                try:
                    curses.curs_set(0)
                except curses.error:
                    pass
            break

        self._draw_input_border("")
        self.log(f"> {prompt} {text}".rstrip(), style="accent")
        return text

    def run_with_spinner(self, label, fn, *args, **kwargs):
        result = {}

        def target():
            try:
                result["value"] = fn(*args, **kwargs)
            except Exception as e:  # noqa: BLE001 - surfaced to the caller below
                result["error"] = e

        thread = threading.Thread(target=target, daemon=True)
        thread.start()

        self.stdscr.timeout(80)
        i = 0
        try:
            while thread.is_alive():
                self.maybe_resize()
                self._draw_status(f"{_SPINNER[i % len(_SPINNER)]}  {label}")
                i += 1
                ch = self.stdscr.getch()
                if ch in (curses.ascii.ETX, curses.ascii.ESC):
                    raise _Quit
        finally:
            self.stdscr.timeout(-1)
            self._draw_status("")

        if "error" in result:
            raise result["error"]
        return result.get("value")


def _main(stdscr):
    lines, cols = stdscr.getmaxyx()
    if lines < _MIN_LINES or cols < _MIN_COLS:
        raise _TooSmall

    try:
        curses.curs_set(0)
    except curses.error:
        pass
    _init_colors()
    stdscr.bkgd(" ", _COLOR["fg"])
    screen = _Screen(stdscr)
    transcript = []

    screen.log("Enter a YouTube URL to fetch its subtitles.")

    url = screen.ask("YouTube URL:")
    if not subtitle_grabber.is_youtube_url(url):
        msg = "That doesn't look like a YouTube URL."
        screen.log(msg, style="err")
        transcript.append(msg)
        return transcript

    try:
        info = screen.run_with_spinner(
            "Looking up available subtitles...", subtitle_grabber.get_subtitle_options, url
        )
    except RuntimeError as e:
        msg = subtitle_grabber.friendly_error(str(e))
        screen.log(msg, style="err")
        transcript.append(msg)
        return transcript

    if not info["languages"]:
        msg = f'"{info["title"]}" has no subtitles available.'
        screen.log(msg, style="warn")
        transcript.append(msg)
        return transcript

    title_line = f"\"{info['title']}\""
    screen.log(title_line, style="accent")
    transcript.append(title_line)

    codes = sorted(info["languages"])
    screen.log("Available subtitles:")
    for code in codes:
        details = info["languages"][code]
        kind = "auto-generated" if details["auto"] else "official"
        screen.log(f"  {code} - {details['name']} ({kind})")

    default_code = codes[0]
    choice = screen.ask(f"Language code [{default_code}]:") or default_code
    if choice not in info["languages"]:
        msg = f"'{choice}' isn't in the list above."
        screen.log(msg, style="err")
        transcript.append(msg)
        return transcript

    dest_input = screen.ask(f"Save to [{subtitle_grabber.DEFAULT_SUBS_DIR}]:")
    out_dir = Path(dest_input).expanduser() if dest_input else subtitle_grabber.DEFAULT_SUBS_DIR

    try:
        path = screen.run_with_spinner(
            "Downloading...",
            subtitle_grabber.download_subtitle,
            url,
            choice,
            info["languages"][choice]["auto"],
            out_dir,
        )
    except RuntimeError as e:
        msg = subtitle_grabber.friendly_error(str(e))
        screen.log(msg, style="err")
        transcript.append(msg)
        return transcript
    except OSError as e:
        msg = f"Couldn't use that folder: {e.strerror or e}"
        screen.log(msg, style="err")
        transcript.append(msg)
        return transcript

    if path is None:
        msg = "Download finished, but the file couldn't be found afterwards."
        screen.log(msg, style="warn")
        transcript.append(msg)
        return transcript

    msg = f"Saved to: {path}"
    screen.log(msg, style="ok")
    transcript.append(msg)
    return transcript


def run():
    try:
        transcript = curses.wrapper(_main)
    except (_Quit, KeyboardInterrupt):
        print("\nCancelled.")
        return
    except _TooSmall:
        print(f"Terminal too small (need at least {_MIN_COLS}x{_MIN_LINES}). Resize and try again.")
        return

    for line in transcript:
        print(line)


if __name__ == "__main__":
    run()
