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
        "en": None,  # No translation needed for English
        "hi": MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-en-hi"),
        "fr": MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-en-fr"),
        "de": MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-en-de"),
        "es": MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-en-es"),
    }
    translation_tokenizers = {
        "en": None,
        "hi": MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-hi"),
        "fr": MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-fr"),
        "de": MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-de"),
        "es": MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-es"),
    }
    return translation_models, translation_tokenizers


def _chunk_text(text, max_words=350):
    """Split text into chunks of at most max_words words."""
    words = text.split()
    return [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)]


def translate_text(text, target_lang, models, tokenizers):
    """
    Translates text to a specified target language using pre-loaded MarianMT models.
    Long texts are split into chunks to stay within the model's token limit.
    """
    if target_lang == "en":
        return text

    if target_lang not in models:
        st.warning(f"Translation to {target_lang.upper()} is not supported. Returning original text.")
        return text

    model = models[target_lang]
    tokenizer = tokenizers[target_lang]

    try:
        chunks = _chunk_text(text, max_words=350)
        translated_chunks = []
        for chunk in chunks:
            inputs = tokenizer.encode(chunk, return_tensors="pt", truncation=True, max_length=512)
            translated_tokens = model.generate(inputs, max_length=512, num_beams=4, early_stopping=True)
            translated_chunks.append(tokenizer.decode(translated_tokens[0], skip_special_tokens=True))
        return " ".join(translated_chunks)
    except Exception as e:
        st.error(f"❌ Error during translation to {target_lang.upper()}: {e}. Returning original text.")
        return text


# --- Summarization Functions ---
@st.cache_resource
def load_summarizer():
    """
    Loads a summarization pipeline using BART.
    The pipeline is cached for performance.
    """
    return pipeline("summarization", model="facebook/bart-large-cnn")


def summarize_text(text, summarizer_pipeline, max_length=150, min_length=50):
    """
    Summarizes the given text using the loaded summarization pipeline.
    Long texts are split into chunks; each chunk is summarized and the
    partial summaries are joined for a final pass.
    """
    words = text.split()
    if len(words) < 50:
        st.info("Text is too short for effective summarization. Returning original text.")
        return text

    try:
        # BART handles up to ~1024 tokens; use 500-word chunks to stay safe
        chunks = _chunk_text(text, max_words=500)
        partial_summaries = []
        for chunk in chunks:
            result = summarizer_pipeline(
                chunk,
                max_length=max_length,
                min_length=min(min_length, max(10, len(chunk.split()) // 2)),
                do_sample=False,
            )
            partial_summaries.append(result[0]["summary_text"])

        # If multiple chunks produced multiple summaries, do one final pass
        if len(partial_summaries) > 1:
            combined = " ".join(partial_summaries)
            if len(combined.split()) >= 50:
                final = summarizer_pipeline(
                    combined,
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=False,
                )
                return final[0]["summary_text"]
        return partial_summaries[0]
    except Exception as e:
        st.error(f"❌ Error during summarization: {e}. Returning original text.")
        return text
