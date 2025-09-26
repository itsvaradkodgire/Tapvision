import streamlit as st
import pytesseract
from PIL import Image
from docx import Document
import fitz # PyMuPDF
import requests
from bs4 import BeautifulSoup
from ebooklib import epub
import socket
import os

# Set Tesseract CMD path if not in system PATH
# On Windows, it might be:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# Ensure Tesseract is installed and its path is correctly set.

# --- File Reading Functions ---
def read_image(file_obj):
    """Extracts text from an image file using OCR (Tesseract)."""
    try:
        img = Image.open(file_obj)
        text = pytesseract.image_to_string(img)
        return text
    except pytesseract.TesseractNotFoundError:
        st.error(
            "❌ Tesseract OCR not found. Please install Tesseract "
            "and ensure its executable path is correctly set in your environment "
            "or in the script (`pytesseract.pytesseract.tesseract_cmd = ...`)."
        )
        return ""
    except Exception as e:
        st.error(f"❌ Error reading image: {e}")
        return ""

def read_pdf(file_obj):
    """Extracts text from a PDF file."""
    try:
        # PyMuPDF expects bytes-like object or path
        doc = fitz.open(stream=file_obj.read(), filetype="pdf")
        text = "".join(page.get_text() for page in doc)
        doc.close()
        return text
    except Exception as e:
        st.error(f"❌ Error reading PDF: {e}")
        return ""

def read_word(file_obj):
    """Extracts text from a Word document (DOCX)."""
    try:
        doc = Document(file_obj)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)
    except Exception as e:
        st.error(f"❌ Error reading Word document: {e}")
        return ""

def read_epub(file_obj):
    """Extracts text from an ePub file."""
    try:
        book = epub.read_epub(file_obj)
        text = ""
        for item in book.get_items():
            if item.get_type() == epub.EpubHtml:
                soup = BeautifulSoup(item.content, 'html.parser')
                # Get text, clean it up, and append
                text += soup.get_text(separator=' ', strip=True) + "\n"
        return text
    except Exception as e:
        st.error(f"❌ Error reading ePub: {e}")
        return ""

def read_plain_text(file_obj):
    """Extracts text from a plain text file."""
    try:
        # Decode using utf-8, with a fallback to latin-1 if utf-8 fails
        return file_obj.read().decode("utf-8", errors='ignore')
    except Exception as e:
        st.error(f"❌ Error reading plain text file: {e}")
        return ""

def read_web_page(url):
    """Fetches and extracts readable text content from a web page."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script, style, and navigation elements
        for script_or_style in soup(["script", "style", "nav", "footer", "header"]):
            script_or_style.extract()

        # Get text and clean up whitespace
        text = soup.get_text(separator=' ', strip=True)
        return text

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            st.error("🚫 This website doesn't allow extracting data (HTTP 403 Forbidden). Try another website.")
        else:
            st.error(f"🌐 HTTP Error fetching URL: {e}")
        return ""
    except requests.exceptions.ConnectionError as e:
        st.error(f"🌐 Connection Error: Could not connect to the URL '{url}'. Check your internet connection or URL.")
        return ""
    except requests.exceptions.Timeout:
        st.error(f"🌐 Timeout Error: The request to '{url}' took too long. The website might be slow or unresponsive.")
        return ""
    except requests.exceptions.RequestException as e:
        st.error(f"🌐 Error fetching URL: {e}")
        return ""
    except Exception as e:
        st.error(f"❌ An unexpected error occurred while processing the URL: {e}")
        return ""

# --- Main Text Reading Dispatcher ---
def read_text(file_obj=None, file_type=None, url=None):
    """
    Dispatches to the correct reading function based on input type.
    Returns the extracted text as a string.
    """
    if url:
        return read_web_page(url)
    elif file_obj and file_type:
        if file_type == 'pdf':
            return read_pdf(file_obj)
        elif file_type == 'docx':
            return read_word(file_obj)
        elif file_type == 'epub':
            return read_epub(file_obj)
        elif file_type == 'txt':
            return read_plain_text(file_obj)
        elif file_type in ['jpg', 'jpeg', 'png']:
            return read_image(file_obj)
        else:
            st.error(f"Unsupported file format: {file_type}")
            return ""
    return ""

def is_internet_available():
    """Checks if there's an active internet connection."""
    try:
        # Try to connect to Google's DNS server
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False
