import streamlit as st
import os
from text_utils import read_text, is_internet_available
from speech_utils import recognize_speech_from_mic, text_to_speech_auto
from nlp_utils import load_translation_models, translate_text, load_summarizer, summarize_text

# --- Configuration and Initializations ---
st.set_page_config(page_title="TapVision: Text & Speech AI", layout="wide", initial_sidebar_state="expanded")

# Load NLP models (cached for performance)
translation_models, translation_tokenizers = load_translation_models()
summarizer_pipeline = load_summarizer()

# Tesseract command for OCR (Update this path if Tesseract isn't in your PATH)
# If you're on Windows, it might look like:
# import pytesseract
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# Ensure Tesseract is installed and its path is correctly set.

# --- Streamlit UI ---
st.sidebar.title("About TapVision")
st.sidebar.info(
    "TapVision is an intelligent application designed to make information "
    "accessible. It extracts text from various sources, translates, summarizes, "
    "and converts it into speech, all through intuitive interactions."
)
st.sidebar.markdown("---")
st.sidebar.markdown("Developed with ❤️ using Streamlit, Hugging Face, and more.")


st.title("🧲 TapVision: Text & Speech AI")
st.markdown("### Extract, Translate, Summarize, and Listen to Your Content!")

# --- Input Section ---
st.subheader("1. Provide Your Content")
input_method = st.radio(
    "Choose your input method:",
    ['Upload File', 'Enter URL', 'Paste Text'],
    key="input_method",
    horizontal=True
)

content = ""
uploaded_file = None
url_input = ""
pasted_text = ""

if input_method == 'Upload File':
    uploaded_file = st.file_uploader(
        "📂 Upload a file (PDF, DOCX, EPUB, TXT, or Image)",
        type=["pdf", "docx", "epub", "txt", "jpg", "jpeg", "png"]
    )
    if uploaded_file:
        MAX_SIZE_MB = 50  # Limit file size to 50MB to prevent issues
        uploaded_file.seek(0, 2)
        file_size = uploaded_file.tell() / (1024 * 1024)
        uploaded_file.seek(0)
        if file_size > MAX_SIZE_MB:
            st.error(f"File too large! {file_size:.2f} MB exceeds {MAX_SIZE_MB} MB limit. Please upload a smaller file.")
        else:
            file_type = uploaded_file.name.split(".")[-1].lower()
            with st.spinner(f"Extracting text from {file_type.upper()}..."):
                content = read_text(file_obj=uploaded_file, file_type=file_type)

elif input_method == 'Enter URL':
    url_input = st.text_input("🌐 Enter a URL (e.g., https://www.example.com)")
    if url_input:
        if not is_internet_available():
            st.error("❌ No internet connection detected. Please check your connection to fetch content from a URL.")
        else:
            with st.spinner("Fetching and extracting text from URL..."):
                content = read_text(url=url_input)

elif input_method == 'Paste Text':
    pasted_text = st.text_area("✍️ Paste your text here", height=200)
    if pasted_text:
        content = pasted_text.strip()

# Display extracted/pasted content
if content:
    st.subheader("2. Extracted Content")
    st.info("Review the extracted text below.")
    st.text_area("📝 Content for Processing", content, height=300, key="original_content_display")
else:
    st.warning("No content available for processing. Please upload a file, enter a URL, or paste text.")

# --- Processing Section (Summarize, Translate, Speak) ---
if content:
    st.subheader("3. Process Your Content")

    processed_content = content # Start with the original/extracted content

    # Summarization
    st.markdown("#### Summarization")
    st.info("Say 'summarize' to get a concise version of the text.")
    if st.button("🎤 Ask to Summarize"):
        command = recognize_speech_from_mic()
        if command:
            if any(word in command.lower() for word in ["summarize", "sumarize", "summarise"]):
                with st.spinner("Summarizing text..."):
                    processed_content = summarize_text(processed_content, summarizer_pipeline)
                st.success("Text summarized successfully!")
                st.text_area("📖 Summarized Text", processed_content, height=200, key="summarized_content_display")
            else:
                st.warning("Command not recognized. Please say 'summarize'.")
        else:
            st.warning("Speech recognition failed. Please try again.")

    # Translation
    st.markdown("#### Translation")
    st.info("Say 'translate to [language]' (e.g., 'translate to Hindi', 'translate to French').")
    language_command = st.text_input("Or type desired translation language (e.g., 'Hindi', 'French', 'German', 'English'):", key="lang_type_input")
    selected_language_code = "en" # Default to English

    if st.button("🎤 Ask to Translate") or language_command:
        if not language_command: # If button is clicked but no text input
            lang_voice_command = recognize_speech_from_mic(
                "\U0001f3a4 Listening for translation language (e.g., English, Hindi, French, German)..."
            )
            if lang_voice_command:
                language_command = lang_voice_command

        language_mapping = {
            "english": "en", "hindi": "hi", "french": "fr", "german": "de",
            # Add more as needed based on your models
        }
        normalized_lang_input = language_command.lower().strip()
        selected_language_code = language_mapping.get(normalized_lang_input, "en")

        if selected_language_code == "en" and normalized_lang_input not in ["english", "en", ""]:
            st.warning(f"Language '{language_command}' not fully supported for translation. Defaulting to English (no translation).")

        with st.spinner(f"Translating to {language_command or 'English'}..."):
            translated_text = translate_text(processed_content, selected_language_code,
                                             translation_models, translation_tokenizers)
        st.text_area("🌍 Translated Text", translated_text, height=200, key="translated_content_display")
        processed_content = translated_text # Use translated text for speech

    # Text-to-Speech
    st.markdown("#### Text-to-Speech")
    st.info("Say 'convert to speech' to hear the current text.")
    if st.button("🎤 Convert to Speech"):
        command = recognize_speech_from_mic()
        if command and "convert to speech" in command.lower():
            if not processed_content.strip():
                st.error("No text available to convert to speech. Please ensure you have content extracted/processed.")
            else:
                speech_language = selected_language_code if 'translated_text' in locals() else "en" # Use translated language if available
                if not is_internet_available() and speech_language != "en":
                    st.warning("Internet connection not available for gTTS (used for non-English speech). Falling back to pyttsx3, which primarily supports English with basic voices.")
                    speech_language = "en" # Force English for pyttsx3 fallback

                with st.spinner(f"Generating audio in {speech_language.upper()}..."):
                    audio_file_path = text_to_speech_auto(processed_content, lang=speech_language)
                    if audio_file_path and os.path.exists(audio_file_path):
                        st.audio(audio_file_path, format="audio/mp3", start_time=0)
                        os.remove(audio_file_path) # Clean up the audio file
                    else:
                        st.error("Failed to generate audio. Please check the text and your internet connection if using non-English languages.")
        else:
            st.warning("Command not recognized. Please say 'convert to speech'.")
