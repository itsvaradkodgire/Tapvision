<div align="center">

# TapVision — Text & Speech AI

**Extract · Translate · Summarize · Listen**

An intelligent NLP-powered web application that turns documents, images, and web pages into accessible, multi-language, spoken content — all in your browser.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Hugging Face](https://img.shields.io/badge/Models-Hugging%20Face-yellow?logo=huggingface&logoColor=white)](https://huggingface.co/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## What is TapVision?

TapVision bridges the gap between raw content and human understanding. Whether you have a scanned PDF, an image full of text, a long article from the web, or a document in a foreign language, TapVision handles the heavy lifting for you.

It chains together five powerful NLP capabilities — **OCR**, **web scraping**, **summarization**, **translation**, and **text-to-speech** — into a single, clean Streamlit interface. You can drive every feature by clicking a button or speaking a voice command.

---

## Features

### Input — Many sources, one workflow

| Method | Formats Supported |
|---|---|
| File Upload | PDF, DOCX, EPUB, TXT, JPG, JPEG, PNG |
| URL Scraping | Any public web page |
| Direct Paste | Raw text |

- **PDF** extraction via PyMuPDF (preserves multi-column layouts)
- **OCR** for images using Tesseract — handles scanned documents and screenshots
- **EPUB** reader that strips HTML markup and delivers clean prose
- **Web scraping** with BeautifulSoup — removes navigation, ads, and boilerplate

---

### Smart Summarization

Powered by **`facebook/bart-large-cnn`** (a BART model fine-tuned on CNN/DailyMail news). Long documents are automatically split into chunks, each summarized individually, and the partial summaries are consolidated into a final cohesive result — so no content is silently dropped regardless of document length.

---

### Multi-language Translation

Powered by **Helsinki-NLP MarianMT** models, the fastest open-source neural translation architecture. Long texts are chunked to respect the 512-token model limit, so entire documents translate correctly.

| Language | Model |
|---|---|
| English → Hindi | `opus-mt-en-hi` |
| English → French | `opus-mt-en-fr` |
| English → German | `opus-mt-en-de` |
| English → Spanish | `opus-mt-en-es` |

---

### Text-to-Speech (TTS)

TapVision intelligently picks the best TTS engine for the situation:

- **Online (gTTS)** — Google Text-to-Speech for high-quality, multi-language audio
- **Offline fallback (pyttsx3)** — runs fully on-device when internet is unavailable; English only

---

### Voice Commands

Interact hands-free using your microphone (powered by Google Web Speech API):

| Say this | Does this |
|---|---|
| *"summarize"* | Summarizes the current content |
| *"translate to Hindi"* | Translates to the named language |
| *"convert to speech"* | Plays the processed text aloud |

Voice and button controls are always available side-by-side — you choose how to interact.

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI Framework | [Streamlit](https://streamlit.io/) |
| Summarization | [facebook/bart-large-cnn](https://huggingface.co/facebook/bart-large-cnn) via Hugging Face Transformers |
| Translation | [Helsinki-NLP MarianMT](https://huggingface.co/Helsinki-NLP) via Hugging Face Transformers |
| OCR | [Tesseract](https://github.com/tesseract-ocr/tesseract) via pytesseract |
| PDF parsing | [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/) |
| DOCX parsing | [python-docx](https://python-docx.readthedocs.io/) |
| EPUB parsing | [ebooklib](https://docs.sourcefab.com/ebooklib/) |
| Web scraping | [requests](https://docs.python-requests.org/) + [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) |
| Text-to-Speech | [gTTS](https://gtts.readthedocs.io/) + [pyttsx3](https://pyttsx3.readthedocs.io/) |
| Speech Recognition | [SpeechRecognition](https://pypi.org/project/SpeechRecognition/) (Google Web Speech API) |

---

## Project Structure

```
TapVision/
├── app.py              # Streamlit UI, session state, user interactions
├── text_utils.py       # File readers (PDF, DOCX, EPUB, TXT, image, URL)
├── nlp_utils.py        # Summarization & translation models + chunking logic
├── speech_utils.py     # TTS (gTTS / pyttsx3) and speech recognition
└── requirements.txt    # Python dependencies
```

---

## Setup and Installation

### Prerequisites

- **Python 3.8+**
- **Tesseract OCR** (required for image-to-text):
  - macOS: `brew install tesseract`
  - Linux (Debian/Ubuntu): `sudo apt-get install tesseract-ocr`
  - Windows: [Download installer from UB Mannheim](https://tesseract-ocr.github.io/tessdoc/Installation.html) and add it to PATH

### Install and Run

```bash
# 1. Clone the repository
git clone https://github.com/itsvaradkodgire/Tapvision.git
cd Tapvision

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the app
streamlit run app.py
```

The app opens automatically at `http://localhost:8501`.

> **Note:** On first run, Hugging Face will download the BART and MarianMT model weights (~1–2 GB total). They are cached locally after that.

---

## Usage Guide

1. **Choose an input method** — upload a file, paste a URL, or type/paste text directly.
2. **Review the extracted content** in the preview panel.
3. **Summarize** — click "Summarize" (or say *"summarize"* via the mic button) to get a concise version.
4. **Translate** — type the target language (e.g. `French`) and click "Translate".
5. **Listen** — click "Convert to Speech" to hear the final processed text in the correct language.

---

## Potential Improvements

This section outlines what could take TapVision from a project to a production-ready product.

### Model & NLP Upgrades
- [ ] **Multilingual summarization** — replace BART with `mBART` or `mT5` to summarize non-English documents directly
- [ ] **Auto language detection** — use `langdetect` to identify the source language and pre-select the right translation direction
- [ ] **More translation pairs** — add Arabic, Chinese, Japanese, Portuguese using existing MarianMT or NLLB-200 models
- [ ] **Better chunking** — use sentence-boundary detection (`nltk.sent_tokenize`) instead of word-count splits for more natural chunk boundaries
- [ ] **Abstractive vs. extractive toggle** — let users choose between BART (abstractive) and `bert-extractive-summarizer` (extractive)

### Input / Extraction
- [ ] **Multi-file batch upload** — process several documents in one session
- [ ] **YouTube / video transcript extraction** — use `youtube-transcript-api` to pull captions
- [ ] **Table & structured data extraction** from PDFs using `camelot` or `pdfplumber`
- [ ] **Image preprocessing** before OCR — deskew, denoise, and binarize with OpenCV for better accuracy

### Voice & Audio
- [ ] **Wake-word detection** — use `pvporcupine` to listen passively without clicking
- [ ] **ElevenLabs / Coqui TTS** integration for more natural, expressive voices
- [ ] **Audio download button** — let users save the generated `.mp3`
- [ ] **Real-time speech-to-text transcript** displayed on screen as the user speaks

### UI / UX
- [ ] **Dark mode** toggle
- [ ] **Processing history** — sidebar log of all processed documents in the current session
- [ ] **Side-by-side view** — original text alongside translated/summarized output
- [ ] **Copy-to-clipboard button** for every output panel
- [ ] **Progress bar** for large document processing

### Performance & Deployment
- [ ] **Async model loading** with a loading screen so the app feels snappy on startup
- [ ] **Docker image** for one-command deployment anywhere
- [ ] **Hugging Face Spaces / Streamlit Community Cloud** deployment for zero-install public access
- [ ] **API mode** — expose core functions (summarize, translate, TTS) as a FastAPI REST service
- [ ] **GPU acceleration** — auto-detect CUDA and move models to GPU for 5–10× faster inference on large documents

---

## Acknowledgements

- [Hugging Face](https://huggingface.co/) for open-source NLP models
- [Helsinki-NLP](https://github.com/Helsinki-NLP) for the MarianMT translation model suite
- [Facebook AI Research](https://ai.facebook.com/) for the BART summarization model
- [Streamlit](https://streamlit.io/) for making ML web apps fast to build

---

<div align="center">
Made with ❤️ by <a href="https://github.com/itsvaradkodgire">Varad Kodgire</a>
</div>
