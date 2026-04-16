import streamlit as st
import os
from text_utils import read_text, is_internet_available
from speech_utils import recognize_speech_from_mic, text_to_speech_auto
from nlp_utils import load_translation_models, translate_text, load_summarizer, summarize_text

# --- Configuration and Initializations ---
st.set_page_config(page_title="TapVision: Text & Speech AI", layout="wide", initial_sidebar_state="expanded")

# Initialize session state
if "content" not in st.session_state:
    st.session_state.content = ""
if "processed_content" not in st.session_state:
    st.session_state.processed_content = ""
if "selected_language_code" not in st.session_state:
    st.session_state.selected_language_code = "en"

# Load NLP models (cached for performance)
translation_models, translation_tokenizers = load_translation_models()
summarizer_pipeline = load_summarizer()

# Supported languages
LANGUAGE_MAP = {
    "english": "en",
    "hindi": "hi",
    "french": "fr",
    "german": "de",
    "spanish": "es",
}

# --- Sidebar ---
st.sidebar.title("About TapVision")
st.sidebar.info(
    "TapVision is an intelligent application designed to make information "
    "accessible. It extracts text from various sources, translates, summarizes, "
    "and converts it into speech, all through intuitive interactions."
)
st.sidebar.markdown("---")
st.sidebar.markdown("**Supported languages:** English, Hindi, French, German, Spanish")
st.sidebar.markdown("---")
st.sidebar.markdown("Developed with ❤️ using Streamlit, Hugging Face, and more.")

# --- Title ---
st.title("🧲 TapVision: Text & Speech AI")
st.markdown("### Extract, Translate, Summarize, and Listen to Your Content!")

# --- Input Section ---
st.subheader("1. Provide Your Content")
input_method = st.radio(
    "Choose your input method:",
    ["Upload File", "Enter URL", "Paste Text"],
    key="input_method",
    horizontal=True,
)

if input_method == "Upload File":
    uploaded_file = st.file_uploader(
        "📂 Upload a file (PDF, DOCX, EPUB, TXT, or Image)",
        type=["pdf", "docx", "epub", "txt", "jpg", "jpeg", "png"],
    )
    if uploaded_file:
        MAX_SIZE_MB = 50
        uploaded_file.seek(0, 2)
        file_size = uploaded_file.tell() / (1024 * 1024)
        uploaded_file.seek(0)
        if file_size > MAX_SIZE_MB:
            st.error(f"File too large! {file_size:.2f} MB exceeds {MAX_SIZE_MB} MB limit.")
        else:
            file_type = uploaded_file.name.split(".")[-1].lower()
            with st.spinner(f"Extracting text from {file_type.upper()}..."):
                extracted = read_text(file_obj=uploaded_file, file_type=file_type)
            if extracted:
                st.session_state.content = extracted
                st.session_state.processed_content = extracted

elif input_method == "Enter URL":
    url_input = st.text_input("🌐 Enter a URL (e.g., https://www.example.com)")
    if url_input:
        if not is_internet_available():
            st.error("❌ No internet connection detected. Please check your connection.")
        else:
            with st.spinner("Fetching and extracting text from URL..."):
                extracted = read_text(url=url_input)
            if extracted:
                st.session_state.content = extracted
                st.session_state.processed_content = extracted

elif input_method == "Paste Text":
    pasted_text = st.text_area("✍️ Paste your text here", height=200)
    if pasted_text:
        st.session_state.content = pasted_text.strip()
        st.session_state.processed_content = pasted_text.strip()

# Display extracted content
if st.session_state.content:
    st.subheader("2. Extracted Content")
    st.info("Review the extracted text below.")
    st.text_area(
        "📝 Content for Processing",
        st.session_state.content,
        height=300,
        key="original_content_display",
    )
else:
    st.warning("No content available. Please upload a file, enter a URL, or paste text.")

# --- Processing Section ---
if st.session_state.content:
    st.subheader("3. Process Your Content")

    # ---- Summarization ----
    st.markdown("#### Summarization")
    col_sum1, col_sum2 = st.columns(2)

    with col_sum1:
        if st.button("📝 Summarize"):
            with st.spinner("Summarizing text..."):
                result = summarize_text(st.session_state.content, summarizer_pipeline)
            st.session_state.processed_content = result
            st.success("Text summarized successfully!")

    with col_sum2:
        if st.button("🎤 Summarize via Voice"):
            command = recognize_speech_from_mic()
            if command and any(w in command.lower() for w in ["summarize", "sumarize", "summarise"]):
                with st.spinner("Summarizing text..."):
                    result = summarize_text(st.session_state.content, summarizer_pipeline)
                st.session_state.processed_content = result
                st.success("Text summarized successfully!")
            elif command:
                st.warning("Command not recognized. Please say 'summarize'.")
            else:
                st.warning("Speech recognition failed. Please try again.")

    if st.session_state.processed_content and st.session_state.processed_content != st.session_state.content:
        st.text_area(
            "📖 Summarized Text",
            st.session_state.processed_content,
            height=200,
            key="summarized_display",
        )

    # ---- Translation ----
    st.markdown("#### Translation")
    st.caption("Supported languages: English, Hindi, French, German, Spanish")

    col_lang, col_voice_lang = st.columns([3, 1])
    with col_lang:
        language_input = st.text_input(
            "Type target language:",
            placeholder="e.g. Hindi, French, German, Spanish, English",
            key="lang_type_input",
        )
    with col_voice_lang:
        st.write("")  # vertical alignment spacer
        voice_lang_btn = st.button("🎤 Speak Language")

    if voice_lang_btn:
        spoken = recognize_speech_from_mic("🎤 Listening for language name...")
        if spoken:
            for name in LANGUAGE_MAP:
                if name in spoken.lower():
                    language_input = name
                    st.info(f"Recognized language: **{name.capitalize()}**")
                    break
            else:
                st.warning(f"Could not match '{spoken}' to a supported language.")

    if st.button("🌍 Translate") and language_input:
        normalized = language_input.lower().strip()
        lang_code = LANGUAGE_MAP.get(normalized, None)
        if lang_code is None:
            st.warning(
                f"Language '{language_input}' is not supported. "
                "Choose from: English, Hindi, French, German, Spanish."
            )
        else:
            st.session_state.selected_language_code = lang_code
            source_text = st.session_state.processed_content or st.session_state.content
            with st.spinner(f"Translating to {language_input.capitalize()}..."):
                translated = translate_text(
                    source_text, lang_code, translation_models, translation_tokenizers
                )
            st.session_state.processed_content = translated
            st.text_area("🌍 Translated Text", translated, height=200, key="translated_display")

    # ---- Text-to-Speech ----
    st.markdown("#### Text-to-Speech")
    tts_source = st.session_state.processed_content or st.session_state.content

    col_tts1, col_tts2 = st.columns(2)

    with col_tts1:
        if st.button("🔊 Convert to Speech"):
            if not tts_source.strip():
                st.error("No text available to convert to speech.")
            else:
                speech_lang = st.session_state.selected_language_code
                if not is_internet_available() and speech_lang != "en":
                    st.warning("No internet — falling back to English (pyttsx3).")
                    speech_lang = "en"
                with st.spinner("Generating audio..."):
                    audio_path = text_to_speech_auto(tts_source, lang=speech_lang)
                if audio_path and os.path.exists(audio_path):
                    st.audio(audio_path, format="audio/mp3")
                    os.remove(audio_path)
                else:
                    st.error("Failed to generate audio. Check your internet connection.")

    with col_tts2:
        if st.button("🎤 Convert to Speech via Voice"):
            command = recognize_speech_from_mic()
            if command and "convert to speech" in command.lower():
                if not tts_source.strip():
                    st.error("No text available to convert to speech.")
                else:
                    speech_lang = st.session_state.selected_language_code
                    with st.spinner("Generating audio..."):
                        audio_path = text_to_speech_auto(tts_source, lang=speech_lang)
                    if audio_path and os.path.exists(audio_path):
                        st.audio(audio_path, format="audio/mp3")
                        os.remove(audio_path)
                    else:
                        st.error("Failed to generate audio.")
            elif command:
                st.warning("Command not recognized. Please say 'convert to speech'.")
            else:
                st.warning("Speech recognition failed. Please try again.")
