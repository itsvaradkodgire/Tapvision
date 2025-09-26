# TapVision: Text & Speech AI

TapVision is an interactive Streamlit application that empowers users to extract text from various sources, translate it into different languages, summarize lengthy content, and convert text into speech, all through an intuitive web interface with voice command capabilities.

## ✨ Features

*   **Multi-format Text Extraction**: Supports PDF, DOCX, EPUB, TXT, and common image formats (JPG, JPEG, PNG) using OCR.
*   **Web Content Extraction**: Extract text from any provided URL.
*   **Text Input**: Paste raw text directly into the application.
*   **Smart Summarization**: Get concise summaries of long articles or documents powered by Hugging Face models.
*   **Multi-language Translation**: Translate extracted or input text into Hindi, French, German, and English using MarianMT models.
*   **Text-to-Speech (TTS)**: Convert processed text into audio.
    *   Utilizes `gTTS` for online, high-quality, multi-language speech.
    *   Falls back to `pyttsx3` for offline English speech.
*   **Voice Commands**: Interact with the application using your voice for summarization, translation, and TTS activation.
*   **Responsive UI**: Built with Streamlit for a clean and user-friendly experience.

## 🚀 Setup and Installation

Follow these steps to get TapVision running on your local machine.

### 1. Prerequisites

*   **Python 3.8+**: Ensure you have a compatible Python version installed.
*   **Tesseract OCR**: For image-to-text functionality, you need Tesseract.
    *   **Windows**: Download and install from [Tesseract at UB Mannheim](https://tesseract-ocr.github.io/tessdoc/Installation.html). Remember the installation path (e.g., `C:\Program Files\Tesseract-OCR\tesseract.exe`). You might need to update the `pytesseract.pytesseract.tesseract_cmd` variable in `text_utils.py` if Tesseract isn't added to your system's PATH.
    *   **macOS**: `brew install tesseract`
    *   **Linux (Debian/Ubuntu)**: `sudo apt-get install tesseract-ocr`

### 2. To run
*  python -m venv venv
*  source venv/bin/activate
*  pip install -r requirements.txt
*  streamlit run app.py



