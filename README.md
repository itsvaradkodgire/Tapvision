<div align="center">

# TapVision — Text & Speech AI

### *Information should be accessible to everyone.*

TapVision is an AI-powered accessibility tool that lets **visually impaired users** extract information from any document, image, or webpage — and have it read aloud, summarized, and translated — entirely hands-free.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Hugging Face](https://img.shields.io/badge/Models-Hugging%20Face-yellow?logo=huggingface&logoColor=white)](https://huggingface.co/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## The Problem

Millions of visually impaired people rely on screen readers and assistive technology every day. But accessing *unstructured* content — a scanned PDF, a photo of a notice board, an article in a foreign language, an EPUB book — still requires significant manual effort. Existing tools either need expensive software, an internet subscription, or a sighted person to help.

**TapVision solves this.** Drop a file. Hear it. That's it.

---

## Two Ways to Use TapVision

### Mode 1 — Hands-Free Auto-Pipeline (`watcher.py`) ✦ *Designed for blind users*

Run once. No browser. No mouse. No screen.

```bash
python watcher.py
```

TapVision watches a folder on your machine (`~/TapVision/inbox/`). The moment you drop a file there — using your screen reader, Finder, a terminal command, or Bluetooth keyboard — it automatically:

1. **Detects** the new file and announces its name
2. **Extracts** all text (OCR for images, full parsing for PDF/DOCX/EPUB)
3. **Summarizes** the content using an AI model
4. **Reads the summary aloud** through your speakers
5. **Listens** for your follow-up voice commands

```
You:          [drop report.pdf into ~/TapVision/inbox/]

TapVision:    "New file detected: report.pdf. Extracting text, please wait."
              "Extraction complete. The document has approximately 1,240 words."
              "Generating a summary."
              "Here is the summary: The report covers Q3 financial results..."

You (voice):  "translate to Hindi"
TapVision:    "Translating to Hindi. Please wait."
              [reads Hindi translation aloud]

You (voice):  "full text"
TapVision:    "Reading the full document now."
              [reads entire document]

You (voice):  "done"
TapVision:    "Going back to waiting for new files."
```

**Voice commands available after every file:**

| Say this | Action |
|---|---|
| `full text` | Read the entire document aloud |
| `repeat` | Hear the summary again |
| `translate to Hindi` | Translate and read in Hindi |
| `translate to French` | Translate and read in French |
| `translate to German` | Translate and read in German |
| `translate to Spanish` | Translate and read in Spanish |
| `done` / `stop` | Return to waiting for the next file |

Processed files are automatically moved to `~/TapVision/processed/` so the inbox stays clean.

---

### Mode 2 — Web App (`app.py`) ✦ *With Accessibility Mode for sighted helpers*

```bash
streamlit run app.py
```

The full browser UI for users who have partial vision, or for a sighted helper assisting someone. Enable **Accessibility Mode** in the sidebar to:

- Automatically read every result aloud the moment it appears (no clicking needed)
- Switch to a **high-contrast black/yellow theme** for low-vision users
- Display larger text throughout the interface

---

## How the Pipeline Works

```
┌─────────────────────────────────────────────────────────┐
│                    INPUT SOURCES                         │
│  PDF │ DOCX │ EPUB │ TXT │ Image (OCR) │ URL │ Paste    │
└────────────────────────┬────────────────────────────────┘
                         │
                    text_utils.py
                         │
                         ▼
              ┌─────────────────────┐
              │   Raw Extracted     │
              │       Text          │
              └──────────┬──────────┘
                         │
                   nlp_utils.py
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    Summarization   Translation    (original)
    (BART model)  (MarianMT model)
          │              │              │
          └──────────────┼──────────────┘
                         │
                  speech_utils.py
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       speak_now()   gTTS (.mp3)   pyttsx3
    [watcher mode]  [web app mode] [offline]
```

---

## Features

### Text Extraction — Any Format

| Source | How |
|---|---|
| PDF | PyMuPDF — preserves multi-column layouts |
| DOCX | python-docx — paragraphs and tables |
| EPUB | ebooklib — strips HTML, delivers clean prose |
| Images (JPG, PNG) | Tesseract OCR — handles scans and photos |
| Plain Text | UTF-8 with latin-1 fallback |
| Any URL | BeautifulSoup — removes ads, nav, footers |

### AI Summarization

Powered by **`facebook/bart-large-cnn`**. Long documents are automatically chunked to stay within the model's token limit — no content is silently dropped regardless of document length. Partial summaries are consolidated into one final result.

### Multi-Language Translation

Powered by **Helsinki-NLP MarianMT** models — fast, open-source, runs locally after first download.

| Language | Model |
|---|---|
| English → Hindi | `opus-mt-en-hi` |
| English → French | `opus-mt-en-fr` |
| English → German | `opus-mt-en-de` |
| English → Spanish | `opus-mt-en-es` |

Long texts are chunked before translation so the full document is translated, not just the first 512 tokens.

### Text-to-Speech

| Engine | When used |
|---|---|
| **gTTS** (Google) | Online — high quality, all 5 languages |
| **pyttsx3** | Offline fallback — English, no internet needed |

In `watcher.py`, audio plays directly through the system speakers (no browser required).

---

## Project Structure

```
TapVision/
├── watcher.py          ← Hands-free auto-pipeline for blind users  ✦ NEW
├── app.py              ← Streamlit web app with Accessibility Mode
├── text_utils.py       ← File readers: PDF, DOCX, EPUB, TXT, image, URL
├── nlp_utils.py        ← Summarization & translation with chunking
├── speech_utils.py     ← TTS (gTTS / pyttsx3) + speak_now() for watcher
└── requirements.txt    ← Python dependencies
```

---

## Setup and Installation

### Prerequisites

- **Python 3.8+**
- **Tesseract OCR** (needed for image-to-text):
  - macOS: `brew install tesseract`
  - Linux: `sudo apt-get install tesseract-ocr`
  - Windows: [Download from UB Mannheim](https://tesseract-ocr.github.io/tessdoc/Installation.html)
- **Audio player for `watcher.py`** (for speaking aloud):
  - macOS: built-in (`afplay`)
  - Linux: `sudo apt-get install mpg123`
  - Windows: built-in (`os.startfile`)

### Install

```bash
git clone https://github.com/itsvaradkodgire/Tapvision.git
cd Tapvision

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

> **First run:** Hugging Face downloads BART and MarianMT weights (~1–2 GB). Cached locally after that.

### Run

```bash
# Hands-free mode (for blind users — no browser needed)
python watcher.py

# Web app mode
streamlit run app.py
```

---

## Ideas for Future Improvements

### Core Accessibility
- [ ] **Wake-word activation** — say *"Hey TapVision"* instead of dropping a file; use `pvporcupine`
- [ ] **Auto language detection** — detect the document's language and skip manual selection (`langdetect`)
- [ ] **Real-time OCR from camera** — point a phone/webcam at any text and hear it immediately (`OpenCV`)
- [ ] **Braille display output** — pipe text to a refreshable Braille display via `liblouis`

### Content & Intelligence
- [ ] **Multilingual summarization** — summarize non-English documents without translating first (`mBART`)
- [ ] **Named entity reading** — announce people, dates, and places with emphasis so they're not missed
- [ ] **Table and figure descriptions** — describe data tables and charts extracted from PDFs
- [ ] **Sentence-boundary chunking** — use `nltk.sent_tokenize` for more natural chunk splits

### Voice & Audio
- [ ] **More expressive voices** — integrate ElevenLabs or Coqui TTS for natural-sounding speech
- [ ] **Adjustable reading speed** — user says *"read slower"* or *"read faster"*
- [ ] **Bookmark by voice** — *"remember this position"* and resume a long document later
- [ ] **Audio download** — save generated `.mp3` for offline listening on any device

### Reach & Distribution
- [ ] **Raspberry Pi / single-board device** — run TapVision on a small device with a physical button; press button, drop file, hear result — zero computer literacy required
- [ ] **WhatsApp / Telegram bot** — send a photo of text to a bot and receive a voice note back
- [ ] **Docker image** — `docker run tapvision` with zero setup
- [ ] **Hugging Face Spaces** — free public URL, no installation for anyone

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web UI | [Streamlit](https://streamlit.io/) |
| Summarization | [facebook/bart-large-cnn](https://huggingface.co/facebook/bart-large-cnn) |
| Translation | [Helsinki-NLP MarianMT](https://huggingface.co/Helsinki-NLP) |
| OCR | [Tesseract](https://github.com/tesseract-ocr/tesseract) via pytesseract |
| PDF | [PyMuPDF](https://pymupdf.readthedocs.io/) |
| DOCX | [python-docx](https://python-docx.readthedocs.io/) |
| EPUB | [ebooklib](https://github.com/aerkalov/ebooklib) |
| Web scraping | requests + BeautifulSoup4 |
| TTS (online) | [gTTS](https://gtts.readthedocs.io/) |
| TTS (offline) | [pyttsx3](https://pyttsx3.readthedocs.io/) |
| Speech input | [SpeechRecognition](https://pypi.org/project/SpeechRecognition/) |
| Folder watching | [watchdog](https://python-watchdog.readthedocs.io/) |

---

## Acknowledgements

- [Hugging Face](https://huggingface.co/) for open-source NLP models
- [Helsinki-NLP](https://github.com/Helsinki-NLP) for the MarianMT translation suite
- [Facebook AI Research](https://ai.facebook.com/) for the BART summarization model
- [Streamlit](https://streamlit.io/) for rapid ML app development

---

<div align="center">

Built with purpose by <a href="https://github.com/itsvaradkodgire">Varad Kodgire</a>

*Making information accessible — one file at a time.*

</div>
