# Manga / Webtoon Translator (Node.js)

Local-first app for translating manga/webtoon images into Myanmar using Node.js, Express, PostgreSQL, Tesseract.js, Sharp and Gemini. Use only content you own or are authorized to process.

## Features
- Import images or ZIP
- Optional HTTPS page import from exact hostnames allowed in .env
- OCR with selectable language
- Batch Gemini translation and editable Myanmar text
- PostgreSQL storage and ZIP export

## Requirements
- Windows 10/11
- Node.js 20+ (npm included)
- PostgreSQL
- Gemini API key for AI translation

## Windows setup
1. In pgAdmin, create database manga_translator.
2. Copy .env.example to .env: `Copy-Item .env.example .env`
3. Set DATABASE_URL and GEMINI_API_KEY in .env. Example:
   `DATABASE_URL=postgresql://postgres:YOUR_URL_ENCODED_PASSWORD@localhost:5432/manga_translator`
   `GEMINI_API_KEY=your_key_here`
   If PostgreSQL uses port 5433, use 5433. URL-encode password characters: # becomes %23 and @ becomes %40.
4. In VS Code terminal run `npm install`, then `npm start`.
5. Open http://localhost:3000.

Tesseract.js downloads OCR language data on first use. OCR can miss stylized text. Typesetting is a first-pass white overlay and needs manual review. A Myanmar-capable font must be available for reliable exported glyphs. Never commit .env/API keys. The app has no login yet; do not expose it publicly before authentication is added. Original Python files remain as a legacy prototype; Node app runs from server.js and public/.
