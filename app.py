import base64
import os
import tempfile

import streamlit as st
from gtts import gTTS

from text_utils import read_text, is_internet_available
from speech_utils import recognize_speech_from_mic, text_to_speech_auto
from nlp_utils import load_translation_models, translate_text, load_summarizer, summarize_text

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TapVision: Text & Speech AI",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state ─────────────────────────────────────────────────────────────
if "content" not in st.session_state:
    st.session_state.content = ""
if "processed_content" not in st.session_state:
    st.session_state.processed_content = ""
if "selected_language_code" not in st.session_state:
    st.session_state.selected_language_code = "en"
if "accessibility_mode" not in st.session_state:
    st.session_state.accessibility_mode = False

# ── Load NLP models (cached) ──────────────────────────────────────────────────
translation_models, translation_tokenizers = load_translation_models()
summarizer_pipeline = load_summarizer()

LANGUAGE_MAP = {
    "english": "en",
    "hindi":   "hi",
    "french":  "fr",
    "german":  "de",
    "spanish": "es",
}

# ── Accessibility helpers ─────────────────────────────────────────────────────

def _autoplay_tts(text, lang="en"):
    """
    Generate audio with gTTS and inject an autoplay <audio> tag.
    Used in Accessibility Mode so results are spoken without any click.
    Silently skips if offline or if text is empty.
    """
    if not text or not text.strip():
        return
    if not is_internet_available():
        return
    # Limit to 300 words so the autoplay isn't overwhelming
    words = text.split()
    if len(words) > 300:
        text = " ".join(words[:300]) + " … content continues."
    try:
        tts = gTTS(text=text, lang=lang)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            path = tmp.name
        tts.save(path)
        with open(path, "rb") as f:
            audio_bytes = f.read()
        os.remove(path)
        b64 = base64.b64encode(audio_bytes).decode()
        st.markdown(
            f'<audio autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>',
            unsafe_allow_html=True,
        )
    except Exception:
        pass  # Non-fatal: user can still click the manual TTS button


def _apply_high_contrast():
    st.markdown(
        """
        <style>
        /* High-contrast accessibility theme */
        .stApp { background-color: #000000 !important; color: #FFFFFF !important; }
        .stTextArea textarea, .stTextInput input {
            background-color: #1a1a1a !important;
            color: #FFFF00 !important;
            font-size: 1.15rem !important;
            border: 2px solid #FFFF00 !important;
        }
        label, .stMarkdown p, .stMarkdown li { color: #FFFFFF !important; font-size: 1.1rem !important; }
        .stButton > button {
            background-color: #FFFF00 !important;
            color: #000000 !important;
            font-weight: bold !important;
            font-size: 1rem !important;
            border: 2px solid #FFFFFF !important;
        }
        .stAlert { border-left: 4px solid #FFFF00 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("TapVision")

# Accessibility Mode toggle
st.session_state.accessibility_mode = st.sidebar.toggle(
    "♿ Accessibility Mode",
    value=st.session_state.accessibility_mode,
    help="Automatically reads every result aloud. Best used with watcher.py for fully hands-free access.",
)

if st.session_state.accessibility_mode:
    _apply_high_contrast()
    st.sidebar.success("Accessibility Mode ON — results will be spoken automatically.")

st.sidebar.markdown("---")
st.sidebar.info(
    "TapVision extracts text from any source, summarizes it, "
    "translates it into your language, and reads it aloud."
)
st.sidebar.markdown("**Supported languages:** English · Hindi · French · German · Spanish")
st.sidebar.markdown("---")

# Watcher callout in sidebar
st.sidebar.markdown("### Hands-Free Mode")
st.sidebar.markdown(
    "For fully automated, screen-free access run:\n"
    "```\npython watcher.py\n```\n"
    "Then drop any file into **~/TapVision/inbox/** — "
    "TapVision will extract, summarize, and read it aloud automatically."
)
st.sidebar.markdown("---")
st.sidebar.markdown("Made with ❤️ for accessibility")

# ── Main UI ───────────────────────────────────────────────────────────────────
st.title("TapVision: Text & Speech AI")
st.markdown("#### Extract · Translate · Summarize · Listen")

# Hands-free banner
if st.session_state.accessibility_mode:
    st.info(
        "♿ **Accessibility Mode is ON.**  "
        "Every result will be read aloud automatically after processing.  "
        "For a fully screen-free experience, run `python watcher.py` instead."
    )

# ── 1. Input ──────────────────────────────────────────────────────────────────
st.subheader("1. Provide Your Content")
input_method = st.radio(
    "Choose your input method:",
    ["Upload File", "Enter URL", "Paste Text"],
    key="input_method",
    horizontal=True,
)

if input_method == "Upload File":
    uploaded_file = st.file_uploader(
        "Upload a file (PDF, DOCX, EPUB, TXT, or Image)",
        type=["pdf", "docx", "epub", "txt", "jpg", "jpeg", "png"],
    )
    if uploaded_file:
        MAX_SIZE_MB = 50
        uploaded_file.seek(0, 2)
        file_size = uploaded_file.tell() / (1024 * 1024)
        uploaded_file.seek(0)
        if file_size > MAX_SIZE_MB:
            st.error(f"File too large ({file_size:.1f} MB). Maximum is {MAX_SIZE_MB} MB.")
        else:
            file_type = uploaded_file.name.rsplit(".", 1)[-1].lower()
            with st.spinner(f"Extracting text from {file_type.upper()}…"):
                extracted = read_text(file_obj=uploaded_file, file_type=file_type)
            if extracted:
                st.session_state.content = extracted
                st.session_state.processed_content = extracted
                if st.session_state.accessibility_mode:
                    word_count = len(extracted.split())
                    _autoplay_tts(f"File loaded. The document contains approximately {word_count} words.")

elif input_method == "Enter URL":
    url_input = st.text_input("Enter a URL (e.g., https://www.example.com)")
    if url_input:
        if not is_internet_available():
            st.error("No internet connection detected.")
        else:
            with st.spinner("Fetching content from URL…"):
                extracted = read_text(url=url_input)
            if extracted:
                st.session_state.content = extracted
                st.session_state.processed_content = extracted
                if st.session_state.accessibility_mode:
                    _autoplay_tts(f"Page loaded. {len(extracted.split())} words extracted.")

elif input_method == "Paste Text":
    pasted_text = st.text_area("Paste your text here", height=200)
    if pasted_text:
        st.session_state.content = pasted_text.strip()
        st.session_state.processed_content = pasted_text.strip()

# ── 2. Preview ────────────────────────────────────────────────────────────────
if st.session_state.content:
    st.subheader("2. Extracted Content")
    st.text_area(
        "Content for Processing",
        st.session_state.content,
        height=250,
        key="original_content_display",
    )
else:
    st.warning("No content yet. Upload a file, enter a URL, or paste text above.")

# ── 3. Process ────────────────────────────────────────────────────────────────
if st.session_state.content:
    st.subheader("3. Process Your Content")

    # ── Summarisation ─────────────────────────────────────────────────────────
    st.markdown("#### Summarization")
    col_s1, col_s2 = st.columns(2)

    with col_s1:
        if st.button("Summarize"):
            with st.spinner("Summarizing…"):
                result = summarize_text(st.session_state.content, summarizer_pipeline)
            st.session_state.processed_content = result
            st.success("Done!")
            st.text_area("Summary", result, height=180, key="sum_display")
            if st.session_state.accessibility_mode:
                _autoplay_tts(f"Summary: {result}")

    with col_s2:
        if st.button("Summarize via Voice"):
            command = recognize_speech_from_mic()
            if command and any(w in command for w in ("summarize", "sumarize", "summarise")):
                with st.spinner("Summarizing…"):
                    result = summarize_text(st.session_state.content, summarizer_pipeline)
                st.session_state.processed_content = result
                st.success("Done!")
                st.text_area("Summary", result, height=180, key="sum_voice_display")
                if st.session_state.accessibility_mode:
                    _autoplay_tts(f"Summary: {result}")
            elif command:
                st.warning("Say 'summarize' to trigger summarization.")
            else:
                st.warning("No speech detected. Please try again.")

    # ── Translation ───────────────────────────────────────────────────────────
    st.markdown("#### Translation")
    st.caption("Supported: English · Hindi · French · German · Spanish")

    col_l1, col_l2 = st.columns([3, 1])
    with col_l1:
        language_input = st.text_input(
            "Target language:",
            placeholder="e.g. Hindi, French, German, Spanish",
            key="lang_input",
        )
    with col_l2:
        st.write("")
        if st.button("Speak Language"):
            spoken = recognize_speech_from_mic("Listening for language name…")
            if spoken:
                for name in LANGUAGE_MAP:
                    if name in spoken.lower():
                        language_input = name
                        st.info(f"Heard: {name.capitalize()}")
                        break
                else:
                    st.warning(f"Could not match '{spoken}' to a supported language.")

    if st.button("Translate") and language_input:
        normalized  = language_input.lower().strip()
        lang_code   = LANGUAGE_MAP.get(normalized)
        if lang_code is None:
            st.warning(f"'{language_input}' is not supported. Choose from: English, Hindi, French, German, Spanish.")
        else:
            st.session_state.selected_language_code = lang_code
            source = st.session_state.processed_content or st.session_state.content
            with st.spinner(f"Translating to {language_input.capitalize()}…"):
                translated = translate_text(source, lang_code, translation_models, translation_tokenizers)
            st.session_state.processed_content = translated
            st.text_area("Translated Text", translated, height=180, key="trans_display")
            if st.session_state.accessibility_mode:
                _autoplay_tts(translated, lang=lang_code)

    # ── Text-to-Speech ────────────────────────────────────────────────────────
    st.markdown("#### Text-to-Speech")
    tts_source = st.session_state.processed_content or st.session_state.content
    col_t1, col_t2 = st.columns(2)

    with col_t1:
        if st.button("Convert to Speech"):
            if not tts_source.strip():
                st.error("No text to convert.")
            else:
                speech_lang = st.session_state.selected_language_code
                if not is_internet_available() and speech_lang != "en":
                    st.warning("No internet — falling back to English.")
                    speech_lang = "en"
                with st.spinner("Generating audio…"):
                    audio_path = text_to_speech_auto(tts_source, lang=speech_lang)
                if audio_path and os.path.exists(audio_path):
                    st.audio(audio_path, format="audio/mp3")
                    os.remove(audio_path)
                else:
                    st.error("Audio generation failed. Check your internet connection.")

    with col_t2:
        if st.button("Convert to Speech via Voice"):
            command = recognize_speech_from_mic()
            if command and "convert to speech" in command.lower():
                speech_lang = st.session_state.selected_language_code
                with st.spinner("Generating audio…"):
                    audio_path = text_to_speech_auto(tts_source, lang=speech_lang)
                if audio_path and os.path.exists(audio_path):
                    st.audio(audio_path, format="audio/mp3")
                    os.remove(audio_path)
                else:
                    st.error("Audio generation failed.")
            elif command:
                st.warning("Say 'convert to speech' to trigger audio.")
            else:
                st.warning("No speech detected. Please try again.")
