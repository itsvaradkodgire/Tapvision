import streamlit as st
import speech_recognition as sr
import pyttsx3
from gtts import gTTS
import os
import sys
import subprocess
import tempfile
from text_utils import is_internet_available


# --- Shared pyttsx3 engine (re-created on error) ---
_tts_engine = None

def _get_pyttsx3_engine():
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = pyttsx3.init()
        _tts_engine.setProperty("rate", 155)   # slightly slower for clarity
    return _tts_engine


def _play_mp3(path):
    """Play an MP3 file using the OS default audio player (no GUI needed)."""
    try:
        if sys.platform == "darwin":
            subprocess.run(["afplay", path], check=True)
        elif sys.platform.startswith("linux"):
            for player in [["mpg123"], ["mpg321"], ["ffplay", "-nodisp", "-autoexit"]]:
                try:
                    subprocess.run(player + [path], check=True,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
                except (FileNotFoundError, subprocess.CalledProcessError):
                    continue
        elif sys.platform == "win32":
            os.startfile(path)
    except Exception as e:
        print(f"[TapVision] Audio playback error: {e}")


def speak_now(text, lang="en"):
    """
    Speak text immediately on the local machine — no browser required.
    Used by watcher.py for the fully hands-free accessibility pipeline.

    - Online + non-English  → gTTS via OS audio player
    - Online + English      → gTTS via OS audio player
    - Offline               → pyttsx3 (English only)
    """
    if not text or not text.strip():
        return

    # Truncate very long passages so the user isn't waiting forever
    words = text.split()
    if len(words) > 300:
        text = " ".join(words[:300]) + " … content continues."

    print(f"[TapVision] Speaking: {text[:80]}{'…' if len(text) > 80 else ''}")

    if is_internet_available():
        try:
            tts = gTTS(text=text, lang=lang)
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                path = tmp.name
            tts.save(path)
            _play_mp3(path)
            os.remove(path)
            return
        except Exception as e:
            print(f"[TapVision] gTTS error: {e} — falling back to pyttsx3")

    # Offline fallback
    try:
        global _tts_engine
        engine = _get_pyttsx3_engine()
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[TapVision] pyttsx3 error: {e}")
        _tts_engine = None  # force re-init next call

# --- Speech Recognition ---
def recognize_speech_from_mic(prompt="\U0001f3a4 Listening... Please speak now.", timeout_seconds=5):
    """
    Recognizes speech from the microphone using Google Web Speech API.
    Provides a prompt and handles common errors.
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info(prompt)
        try:
            recognizer.adjust_for_ambient_noise(source) # Adjust for ambient noise
            audio = recognizer.listen(source, timeout=timeout_seconds)
            command = recognizer.recognize_google(audio)
            st.success(f"🗣️ Recognized: **{command}**")
            return command.lower().strip()
        except sr.WaitTimeoutError:
            st.warning(f"⚠️ No speech detected within {timeout_seconds} seconds. Please try again.")
        except sr.UnknownValueError:
            st.warning("⚠️ Couldn't recognize your voice. Please speak clearly.")
        except sr.RequestError as e:
            st.error(f"❌ Voice recognition service unavailable. Check internet connection or API limits: {e}")
        return None

# --- Text-to-Speech ---
def text_to_speech_with_gtts(text, lang="en"):
    """Converts text to speech using Google Text-to-Speech (online)."""
    if not text.strip():
        st.warning("No text to convert with gTTS.")
        return None
    try:
        tts = gTTS(text=text, lang=lang)
        output_audio_path = f"output_audio_{os.getpid()}.mp3" # Unique file for concurrent runs
        tts.save(output_audio_path)
        return output_audio_path
    except Exception as e:
        st.error(f"❌ Error generating speech with gTTS: {e}. Check internet connection for non-English languages.")
        return None

def text_to_speech_with_pyttsx3(text):
    """Converts text to speech using pyttsx3 (offline). Best for English."""
    if not text.strip():
        st.warning("No text to convert with pyttsx3.")
        return None
    try:
        engine = pyttsx3.init()
        # You can adjust voice properties here if needed
        # voices = engine.getProperty('voices')
        # engine.setProperty('voice', voices[1].id) # Example: set to a female voice
        output_audio_path = f"output_audio_{os.getpid()}.mp3" # Unique file for concurrent runs
        engine.save_to_file(text, output_audio_path)
        engine.runAndWait()
        return output_audio_path
    except Exception as e:
        st.error(f"❌ Error generating speech with pyttsx3: {e}")
        return None

def text_to_speech_auto(text, lang="en"):
    """
    Automatically chooses the best TTS engine:
    - gTTS for non-English languages or if internet is available.
    - pyttsx3 as an offline fallback for English.
    """
    if not text.strip():
        st.error("No text available for speech conversion.")
        return None

    if lang != "en" and not is_internet_available():
        st.warning(f"Internet connection required for {lang.upper()} speech (gTTS). Falling back to pyttsx3, which primarily supports English.")
        return text_to_speech_with_pyttsx3(text) # Pyttsx3 might still try, but quality/language support is limited

    if is_internet_available():
        return text_to_speech_with_gtts(text, lang)
    else:
        # Fallback to pyttsx3 for English if no internet
        if lang == "en":
            return text_to_speech_with_pyttsx3(text)
        else:
            st.error(f"Cannot generate {lang.upper()} speech offline. Please connect to the internet for non-English text-to-speech.")
            return None
