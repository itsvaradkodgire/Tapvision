import streamlit as st
from transformers import MarianMTModel, MarianTokenizer, pipeline

# --- Translation Functions ---
@st.cache_resource
def load_translation_models():
    """
    Loads MarianMT translation models and tokenizers for English to other languages.
    Models are cached to avoid re-loading on every rerun.
    """
    translation_models = {
        "en": None, # No translation needed for English
        "hi": MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-en-hi"), # English to Hindi
        "fr": MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-en-fr"), # English to French
        "de": MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-en-de"), # English to German
        # Add more languages as needed:
        # "es": MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-en-es"), # English to Spanish
    }
    translation_tokenizers = {
        "en": None, # No tokenizer needed for English
        "hi": MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-hi"),
        "fr": MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-fr"),
        "de": MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-de"),
        # "es": MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-es"),
    }
    return translation_models, translation_tokenizers

def translate_text(text, target_lang, models, tokenizers):
    """
    Translates text to a specified target language using pre-loaded MarianMT models.
    """
    if target_lang == "en":
        return text # No translation needed for English

    if target_lang not in models:
        st.warning(f"Translation to {target_lang.upper()} is not fully supported or models are not loaded. Returning original text.")
        return text

    model = models[target_lang]
    tokenizer = tokenizers[target_lang]

    try:
        # The MarianMT models usually take input in '>>lang<< text' format
        # but Helsinki-NLP/opus-mt-en-xx models are typically direct.
        # Ensure text is properly encoded and within max_length
        inputs = tokenizer.encode(text, return_tensors="pt", truncation=True, max_length=512)
        translated_tokens = model.generate(inputs, max_length=512, num_beams=4, early_stopping=True)
        translated_text = tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
        return translated_text
    except Exception as e:
        st.error(f"❌ Error during translation to {target_lang.upper()}: {e}. Returning original text.")
        return text

# --- Summarization Functions ---
@st.cache_resource
def load_summarizer():
    """
    Loads a summarization pipeline (e.g., using BART).
    The pipeline is cached for performance.
    """
    # Using 'facebook/bart-large-cnn' is good for general news summarization.
    # 't5-small' or 't5-base' are smaller alternatives if performance is critical,
    # but might require adding "summarize: " prefix to input.
    return pipeline("summarization", model="facebook/bart-large-cnn")

def summarize_text(text, summarizer_pipeline, max_length=150, min_length=50):
    """
    Summarizes the given text using the loaded summarization pipeline.
    Adds a check for minimum text length before summarizing.
    """
    # Simple heuristic: don't summarize very short texts
    if len(text.split()) < 50:
        st.info("Text is too short for effective summarization. Returning original text.")
        return text

    try:
        # The summarizer often works better with a single string
        summary = summarizer_pipeline(
            text,
            max_length=max_length,
            min_length=min_length,
            do_sample=False # For consistent output
        )
        return summary[0]['summary_text']
    except Exception as e:
        st.error(f"❌ Error during summarization: {e}. Returning original text.")
        return text
