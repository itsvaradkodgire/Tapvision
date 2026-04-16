#!/usr/bin/env python3
"""
TapVision Auto-Pipeline  —  Hands-Free Accessibility Mode
==========================================================
Designed for visually impaired users who cannot interact with a browser UI.

HOW IT WORKS
------------
1. Run this script once:  python watcher.py
2. TapVision announces itself and starts watching ~/TapVision/inbox/
3. Drop ANY supported file into that folder (PDF, DOCX, EPUB, TXT,
   JPG, PNG) — using your screen reader, Finder, terminal, or any
   method you prefer.
4. TapVision automatically:
      • Detects the file
      • Extracts all text (OCR for images)
      • Summarizes the content
      • Reads the summary aloud
      • Listens for your follow-up voice commands
5. Processed files are moved to ~/TapVision/processed/ so the inbox
   stays clean.

VOICE COMMANDS (after a file is read)
--------------------------------------
  "full text"          — Read the entire document aloud
  "translate to Hindi" — Translate summary to Hindi, French, German,
  "translate to French"  Spanish, or English, then read it
  "repeat"             — Hear the summary again
  "done" / "stop"      — Return to waiting for the next file

REQUIREMENTS
------------
  pip install -r requirements.txt
  # Plus Tesseract OCR for images: brew install tesseract (macOS)
"""

import os
import sys
import time
import threading

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from text_utils import read_text, is_internet_available
from speech_utils import speak_now, recognize_speech_from_mic

# ── Folders ──────────────────────────────────────────────────────────────────
INBOX_FOLDER     = os.path.expanduser("~/TapVision/inbox")
PROCESSED_FOLDER = os.path.expanduser("~/TapVision/processed")
ERROR_FOLDER     = os.path.expanduser("~/TapVision/errors")

SUPPORTED_EXTENSIONS = {"pdf", "docx", "epub", "txt", "jpg", "jpeg", "png"}

LANGUAGE_MAP = {
    "hindi":   "hi",
    "french":  "fr",
    "german":  "de",
    "spanish": "es",
    "english": "en",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _wait_until_stable(filepath, poll_interval=0.4, stable_for=1.0, timeout=30):
    """
    Wait until the file size stops changing (i.e., the copy/write is done).
    Returns True if the file stabilised, False if it timed out.
    """
    deadline = time.time() + timeout
    last_size = -1
    stable_since = None

    while time.time() < deadline:
        try:
            size = os.path.getsize(filepath)
        except OSError:
            time.sleep(poll_interval)
            continue

        if size == last_size:
            if stable_since is None:
                stable_since = time.time()
            elif time.time() - stable_since >= stable_for:
                return True
        else:
            last_size = size
            stable_since = None

        time.sleep(poll_interval)

    return False


def _move_file(src, dest_folder):
    os.makedirs(dest_folder, exist_ok=True)
    base = os.path.basename(src)
    dest = os.path.join(dest_folder, base)
    # Avoid overwriting existing files in destination
    if os.path.exists(dest):
        name, ext = os.path.splitext(base)
        dest = os.path.join(dest_folder, f"{name}_{int(time.time())}{ext}")
    try:
        os.rename(src, dest)
    except OSError:
        pass  # Non-fatal; leave file in place


# ── Event Handler ─────────────────────────────────────────────────────────────

class TapVisionHandler(FileSystemEventHandler):
    """Processes every new file that lands in the inbox folder."""

    def __init__(self, summarizer, translation_models, translation_tokenizers):
        self.summarizer             = summarizer
        self.translation_models     = translation_models
        self.translation_tokenizers = translation_tokenizers
        self._lock                  = threading.Lock()  # one file at a time

    # ── watchdog callback ─────────────────────────────────────────────────────

    def on_created(self, event):
        if event.is_directory:
            return
        # Run processing in a thread so the Observer loop stays unblocked
        t = threading.Thread(target=self._handle, args=(event.src_path,), daemon=True)
        t.start()

    # ── main processing flow ──────────────────────────────────────────────────

    def _handle(self, filepath):
        with self._lock:
            self._process(filepath)

    def _process(self, filepath):
        filename = os.path.basename(filepath)
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        # ── 1. Validate extension ─────────────────────────────────────────────
        if ext not in SUPPORTED_EXTENSIONS:
            speak_now(
                f"Skipping {filename}. "
                f"Supported formats are PDF, Word, EPUB, plain text, and images."
            )
            return

        # ── 2. Wait for the file to finish writing ────────────────────────────
        speak_now(f"New file detected: {filename}. Please wait while I prepare it.")
        if not _wait_until_stable(filepath):
            speak_now("The file took too long to appear. Please try again.")
            return

        # ── 3. Extract text ───────────────────────────────────────────────────
        speak_now("Extracting text now.")
        try:
            with open(filepath, "rb") as fobj:
                text = read_text(file_obj=fobj, file_type=ext)
        except Exception as e:
            speak_now(f"Sorry, I could not open the file. {e}")
            _move_file(filepath, ERROR_FOLDER)
            return

        if not text or not text.strip():
            speak_now(
                "I could not find any readable text in this file. "
                "If it is a scanned image, make sure Tesseract OCR is installed."
            )
            _move_file(filepath, ERROR_FOLDER)
            return

        word_count = len(text.split())
        speak_now(f"Extraction complete. The document has approximately {word_count} words.")

        # ── 4. Summarise ──────────────────────────────────────────────────────
        from nlp_utils import summarize_text   # imported here to keep startup fast

        if word_count >= 50:
            speak_now("Generating a summary. This may take a moment.")
            try:
                summary = summarize_text(text, self.summarizer)
            except Exception as e:
                speak_now(f"Summarization failed: {e}. I will read the first part of the document instead.")
                summary = " ".join(text.split()[:120])
        else:
            summary = text
            speak_now("The document is short, so I will read it directly.")

        # ── 5. Read summary aloud ─────────────────────────────────────────────
        speak_now(f"Here is the summary: {summary}")

        # ── 6. Archive the file ───────────────────────────────────────────────
        _move_file(filepath, PROCESSED_FOLDER)

        # ── 7. Voice follow-up menu ───────────────────────────────────────────
        self._voice_menu(text, summary)

    # ── interactive voice menu ─────────────────────────────────────────────────

    def _voice_menu(self, full_text, summary):
        from nlp_utils import translate_text   # lazy import

        speak_now(
            "What would you like to do? "
            "Say: full text to hear everything, "
            "translate to followed by a language name, "
            "repeat to hear the summary again, "
            "or done to wait for the next file."
        )

        consecutive_misses = 0

        while consecutive_misses < 3:
            command = recognize_speech_from_mic(
                prompt="Listening for your command...",
                timeout_seconds=8,
            )

            if not command:
                consecutive_misses += 1
                if consecutive_misses < 3:
                    speak_now("I did not catch that. Please try again.")
                continue

            consecutive_misses = 0
            command = command.lower().strip()

            if any(k in command for k in ("full text", "read all", "read everything", "everything")):
                speak_now("Reading the full document now.")
                speak_now(full_text)

            elif "repeat" in command or "again" in command or "summary" in command:
                speak_now(summary)

            elif "translate" in command:
                target_code = None
                for lang_name, code in LANGUAGE_MAP.items():
                    if lang_name in command:
                        target_code = code
                        lang_display = lang_name.capitalize()
                        break

                if target_code and target_code != "en":
                    speak_now(f"Translating to {lang_display}. Please wait.")
                    try:
                        translated = translate_text(
                            summary, target_code,
                            self.translation_models,
                            self.translation_tokenizers,
                        )
                        speak_now(translated, lang=target_code)
                    except Exception as e:
                        speak_now(f"Translation failed. {e}")
                elif target_code == "en":
                    speak_now("The content is already in English.")
                else:
                    speak_now(
                        "I did not recognise the language. "
                        "Supported languages are Hindi, French, German, Spanish, and English."
                    )
                    continue

            elif any(k in command for k in ("done", "stop", "exit", "next", "finish")):
                speak_now("Going back to waiting for new files. Drop a file into the inbox folder whenever you are ready.")
                return

            else:
                speak_now(
                    "Command not recognised. "
                    "Say full text, translate to a language, repeat, or done."
                )
                continue

            # After each action offer another command
            speak_now("Anything else? Say a command, or say done to finish.")


# ── Entry Point ───────────────────────────────────────────────────────────────

def main():
    # ── Create folders ────────────────────────────────────────────────────────
    for folder in (INBOX_FOLDER, PROCESSED_FOLDER, ERROR_FOLDER):
        os.makedirs(folder, exist_ok=True)

    print("=" * 62)
    print("  TapVision  —  Hands-Free Auto-Pipeline")
    print(f"  Inbox:     {INBOX_FOLDER}")
    print(f"  Processed: {PROCESSED_FOLDER}")
    print("  Press Ctrl+C to stop.")
    print("=" * 62)

    # ── Load models (cached after first run) ──────────────────────────────────
    speak_now(
        "Loading TapVision. "
        "Please wait while the AI models are initialised. "
        "This takes about one minute on the first run."
    )
    print("\nLoading NLP models…")

    from nlp_utils import load_summarizer, load_translation_models
    summarizer = load_summarizer()
    translation_models, translation_tokenizers = load_translation_models()

    print("Models ready.\n")
    speak_now(
        "TapVision is ready. "
        f"I am watching your TapVision inbox folder. "
        "Drop any PDF, Word document, EPUB, text file, or image there "
        "and I will read it to you automatically."
    )

    # ── Start folder watcher ──────────────────────────────────────────────────
    handler  = TapVisionHandler(summarizer, translation_models, translation_tokenizers)
    observer = Observer()
    observer.schedule(handler, INBOX_FOLDER, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        speak_now("TapVision is shutting down. Goodbye.")
        print("\nStopped.")

    observer.join()


if __name__ == "__main__":
    main()
