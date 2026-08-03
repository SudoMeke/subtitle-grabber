import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import subtitle_grabber as sg


def fake_result(returncode=0, stdout="", stderr=""):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


class IsYoutubeUrlTests(unittest.TestCase):
    def test_accepts_youtube_com(self):
        self.assertTrue(sg.is_youtube_url("https://www.youtube.com/watch?v=abc123"))

    def test_accepts_youtu_be(self):
        self.assertTrue(sg.is_youtube_url("https://youtu.be/abc123"))

    def test_rejects_other_urls(self):
        self.assertFalse(sg.is_youtube_url("https://vimeo.com/12345"))

    def test_rejects_non_url_text(self):
        self.assertFalse(sg.is_youtube_url("not a url"))


class IsRealCaptionTests(unittest.TestCase):
    def test_real_caption_has_no_tlang(self):
        self.assertTrue(sg._is_real_caption({"url": "https://example.com/caption.vtt"}))

    def test_auto_translated_caption_is_excluded(self):
        self.assertFalse(sg._is_real_caption({"url": "https://example.com/caption.vtt?tlang=fr"}))

    def test_missing_url_treated_as_real(self):
        self.assertTrue(sg._is_real_caption({}))


class FriendlyErrorTests(unittest.TestCase):
    def test_private_video(self):
        self.assertEqual(sg.friendly_error("ERROR: Private video"), "That video is private.")

    def test_unavailable_video(self):
        self.assertEqual(
            sg.friendly_error("Video unavailable"),
            "That video is unavailable (deleted or region-blocked).",
        )

    def test_sign_in_required(self):
        self.assertEqual(
            sg.friendly_error("Sign in to confirm your age"),
            "That video requires sign-in and can't be downloaded here.",
        )

    def test_missing_yt_dlp(self):
        self.assertEqual(
            sg.friendly_error("No module named yt_dlp"),
            "yt-dlp isn't installed. Run: pip install -r requirements.txt",
        )

    def test_unknown_error_falls_back(self):
        self.assertEqual(
            sg.friendly_error("some unexpected failure"),
            "Couldn't read that video. Double-check the URL and try again.",
        )


class GetSubtitleOptionsTests(unittest.TestCase):
    @patch("subtitle_grabber._run")
    def test_raises_on_nonzero_returncode(self, mock_run):
        mock_run.return_value = fake_result(returncode=1, stderr="ERROR: Video unavailable\n")
        with self.assertRaises(RuntimeError) as ctx:
            sg.get_subtitle_options("https://youtu.be/abc")
        self.assertEqual(str(ctx.exception), "ERROR: Video unavailable")

    @patch("subtitle_grabber._run")
    def test_collects_manual_and_automatic_subtitles(self, mock_run):
        info = {
            "title": "Test Video",
            "subtitles": {
                "en": [{"name": "English", "url": "https://example.com/en.vtt"}],
            },
            "automatic_captions": {
                "en": [{"name": "English (auto)", "url": "https://example.com/en-auto.vtt"}],
                "fr": [{"name": "French", "url": "https://example.com/fr.vtt"}],
                "de": [{"name": "German (translated)", "url": "https://example.com/de.vtt?tlang=de"}],
            },
        }
        import json

        mock_run.return_value = fake_result(returncode=0, stdout=json.dumps(info))
        result = sg.get_subtitle_options("https://youtu.be/abc")

        self.assertEqual(result["title"], "Test Video")
        # "en" has a manual track, so the automatic one must not override it.
        self.assertEqual(result["languages"]["en"], {"name": "English", "auto": False})
        self.assertEqual(result["languages"]["fr"], {"name": "French", "auto": True})
        # "de" only has an auto-translated caption (tlang=), so it's excluded.
        self.assertNotIn("de", result["languages"])

    @patch("subtitle_grabber._run")
    def test_no_subtitles_available(self, mock_run):
        import json

        mock_run.return_value = fake_result(returncode=0, stdout=json.dumps({"title": "No Subs"}))
        result = sg.get_subtitle_options("https://youtu.be/abc")
        self.assertEqual(result, {"title": "No Subs", "languages": {}})


class DownloadSubtitleTests(unittest.TestCase):
    @patch("subtitle_grabber._run")
    def test_raises_on_nonzero_returncode(self, mock_run):
        mock_run.return_value = fake_result(returncode=1, stderr="ERROR: Private video\n")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RuntimeError) as ctx:
                sg.download_subtitle("https://youtu.be/abc", "en", False, out_dir=Path(tmp))
        self.assertEqual(str(ctx.exception), "ERROR: Private video")

    @patch("subtitle_grabber._run")
    def test_returns_newly_created_file(self, mock_run):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            (out_dir / "Existing Video.en.srt").touch()

            def create_file(args):
                (out_dir / "New Video.en.srt").touch()
                return fake_result(returncode=0)

            mock_run.side_effect = create_file
            path = sg.download_subtitle("https://youtu.be/abc", "en", False, out_dir=out_dir)
            self.assertEqual(path.name, "New Video.en.srt")

    @patch("subtitle_grabber._run")
    def test_falls_back_to_lang_glob_when_no_new_file(self, mock_run):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            (out_dir / "Existing Video.en.srt").touch()
            mock_run.return_value = fake_result(returncode=0)

            path = sg.download_subtitle("https://youtu.be/abc", "en", False, out_dir=out_dir)
            self.assertEqual(path.name, "Existing Video.en.srt")

    @patch("subtitle_grabber._run")
    def test_returns_none_when_nothing_found(self, mock_run):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            mock_run.return_value = fake_result(returncode=0)

            path = sg.download_subtitle("https://youtu.be/abc", "en", False, out_dir=out_dir)
            self.assertIsNone(path)

    @patch("subtitle_grabber._run")
    def test_creates_destination_directory(self, mock_run):
        mock_run.return_value = fake_result(returncode=0)
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "nested" / "subs"
            sg.download_subtitle("https://youtu.be/abc", "en", False, out_dir=out_dir)
            self.assertTrue(out_dir.is_dir())


if __name__ == "__main__":
    unittest.main()
