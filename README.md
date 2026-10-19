# Local Manga / Webtoon Translator

A Windows-first local app for translating **content you own or are authorized to process**. It uses Streamlit, PostgreSQL, OCR, and Gemini for Myanmar translation.

## Features
- Import a chapter from local image files or ZIP.
- Optional page URL import, restricted to domains you explicitly allow in `.env`.
- OCR text detection, Myanmar translation, editable OCR/translation rows.
- Save chapters and translations in PostgreSQL.
- Export processed pages as a ZIP.
- Best-effort text cleanup and Myanmar typesetting. Complex art backgrounds may need manual cleanup.

## Requirements
- Windows 10/11
- Python 3.11 (recommended)
- PostgreSQL 15+
- Gemini API key (for AI translation)

## Setup
1. Install PostgreSQL and create a database, for example `manga_translator`.
2. Copy `.env.example` to `.env` and fill in your database URL and Gemini API key.
3. Open PowerShell in this folder:
   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   streamlit run app.py
   ```
4. Open the local address Streamlit prints, usually http://localhost:8501.

If PowerShell blocks activation, run `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` and then `.\.venv\Scripts\python.exe -m streamlit run app.py`.

## URL import safety
URL importing is off unless `ALLOWED_SOURCE_DOMAINS` is configured. Add only domains for which you have permission to retrieve and process images, comma-separated. The app checks the exact host and rejects redirects to other hosts. Do not use this to copy or redistribute material without permission.

## Notes
- OCR accuracy varies by language, font, and image quality.
- The initial cleanup uses inpainting around detected text boxes; review every page before use.
- Never commit `.env` or API keys to GitHub.
