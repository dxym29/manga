import io
import os
import zipfile
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
from PIL import Image
from sqlalchemy import select
from db import init_db, SessionLocal, Chapter, Page, TextItem
from services import (
    fetch_page_images, download_images, image_to_png_bytes, ocr_image,
    translate_texts, clean_text_regions, typeset_text
)

load_dotenv()
st.set_page_config(page_title="Local Manga Translator", page_icon="📚", layout="wide")
st.title("📚 Local Manga / Webtoon Translator")
st.caption("Local-first prototype • PostgreSQL • OCR → Myanmar translation → image export")

try:
    init_db()
except Exception as exc:
    st.error("PostgreSQL connection failed. Check DATABASE_URL in .env and make sure PostgreSQL is running.")
    st.exception(exc)
    st.stop()

with st.sidebar:
    st.header("Settings")
    font_path = st.text_input("Myanmar font file path (TTF/OTF)", placeholder=r"C:\Windows\Fonts\mmrtext.ttf")
    st.caption("Use a Myanmar-capable font such as Pyidaungsu or Noto Sans Myanmar.")
    st.divider()
    st.caption("URL import is disabled until ALLOWED_SOURCE_DOMAINS is configured in .env.")

tab_import, tab_library, tab_review, tab_export = st.tabs(["1 · Import", "2 · Chapters", "3 · OCR / Translate", "4 · Export"])

with tab_import:
    st.subheader("Import chapter images")
    title = st.text_input("Chapter title", value="Chapter 1")
    source_url = st.text_input("Chapter URL (optional)")
    uploaded = st.file_uploader("Upload page images or a ZIP of images", type=["png","jpg","jpeg","webp","zip"], accept_multiple_files=True)
    url_mode = st.checkbox("Try importing image URLs from an allowed chapter page")
    if url_mode and source_url:
        st.warning("Only use URLs you are authorized to retrieve and process.")
        if st.button("Find chapter images"):
            try:
                urls = fetch_page_images(source_url)
                st.session_state["found_urls"] = urls
                st.success(f"Found {len(urls)} same-host image URLs.")
                st.write(urls)
            except Exception as exc:
                st.error(str(exc))
    if st.session_state.get("found_urls"):
        if st.button("Download found images"):
            try:
                imgs = download_images(st.session_state["found_urls"])
                st.session_state["url_images"] = [(name, image_to_png_bytes(img)) for name, img in imgs]
                st.success(f"Downloaded {len(imgs)} images.")
            except Exception as exc:
                st.error(str(exc))
    if st.button("Save chapter", type="primary"):
        prepared = []
        for file in uploaded or []:
            if file.name.lower().endswith(".zip"):
                try:
                    with zipfile.ZipFile(io.BytesIO(file.getvalue())) as zf:
                        for name in sorted(zf.namelist()):
                            if name.lower().endswith((".png",".jpg",".jpeg",".webp")) and not name.startswith("__MACOSX/"):
                                try:
                                    img = Image.open(io.BytesIO(zf.read(name))).convert("RGB")
                                    prepared.append((Path(name).name, image_to_png_bytes(img)))
                                except Exception:
                                    pass
                except zipfile.BadZipFile:
                    st.error(f"Invalid ZIP: {file.name}")
            else:
                try:
                    img = Image.open(io.BytesIO(file.getvalue())).convert("RGB")
                    prepared.append((file.name, image_to_png_bytes(img)))
                except Exception:
                    st.warning(f"Could not read {file.name}")
        prepared.extend(st.session_state.get("url_images", []))
        if not prepared:
            st.error("Upload images/ZIP or download images from an allowed URL first.")
        else:
            with SessionLocal() as db:
                chapter = Chapter(title=title.strip() or "Untitled chapter", source_url=source_url.strip() or None)
                db.add(chapter)
                db.flush()
                for index, (filename, raw) in enumerate(prepared, start=1):
                    db.add(Page(chapter_id=chapter.id, page_number=index, filename=filename, image_bytes=raw))
                db.commit()
                st.session_state.pop("url_images", None)
                st.session_state.pop("found_urls", None)
            st.success(f"Saved {len(prepared)} pages to PostgreSQL.")

def list_chapters():
    with SessionLocal() as db:
        return [(c.id, c.title, len(c.pages), c.created_at.strftime("%Y-%m-%d %H:%M")) for c in db.scalars(select(Chapter).order_by(Chapter.id.desc())).all()]

chapters = list_chapters()
if not chapters:
    st.info("No chapters yet. Import images in the first tab.")
else:
    labels = {f"#{cid} · {ctitle} ({count} pages) · {created}": cid for cid, ctitle, count, created in chapters}
    selected_label = st.selectbox("Active chapter", list(labels.keys()), key="active_chapter")
    selected_id = labels[selected_label]

    with tab_library:
        st.subheader("Saved chapters")
        st.dataframe(pd.DataFrame(chapters, columns=["ID","Title","Pages","Created"]), use_container_width=True, hide_index=True)
        if st.button("Delete selected chapter"):
            with SessionLocal() as db:
                c = db.get(Chapter, selected_id)
                if c:
                    db.delete(c); db.commit()
            st.rerun()

    with tab_review:
        st.subheader("OCR and Myanmar translation")
        with SessionLocal() as db:
            chapter = db.get(Chapter, selected_id)
            page_rows = [(p.id, p.page_number, p.filename, p.image_bytes) for p in chapter.pages]
            text_rows = []
            for p in chapter.pages:
                for item in p.items:
                    text_rows.append({"id":item.id,"page_id":p.id,"page":p.page_number,"source_text":item.source_text,"translated_text":item.translated_text,"x":item.x,"y":item.y,"w":item.w,"h":item.h,"confidence":item.confidence})
        page_options = {f"Page {num}: {name}": (pid, raw) for pid,num,name,raw in page_rows}
        selected_page_label = st.selectbox("Page", list(page_options.keys()))
        selected_page_id, selected_page_raw = page_options[selected_page_label]
        page_image = Image.open(io.BytesIO(selected_page_raw)).convert("RGB")
        st.image(page_image, caption=selected_page_label, use_container_width=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Run OCR on this page"):
                try:
                    detected = ocr_image(page_image)
                    with SessionLocal() as db:
                        db.query(TextItem).filter(TextItem.page_id == selected_page_id).delete()
                        for item in detected:
                            db.add(TextItem(page_id=selected_page_id, source_text=item["text"], translated_text="", x=item["x"], y=item["y"], w=item["w"], h=item["h"], confidence=item["confidence"]))
                        db.commit()
                    st.success(f"Detected {len(detected)} text regions. Review them below.")
                    st.rerun()
                except Exception as exc:
                    st.error("OCR failed. Install Tesseract OCR and check the language data.")
                    st.exception(exc)
        with c2:
            if st.button("Translate all OCR text for this chapter", type="primary"):
                api_key = os.getenv("GEMINI_API_KEY", "").strip()
                try:
                    with SessionLocal() as db:
                        items = db.scalars(select(TextItem).join(Page).where(Page.chapter_id == selected_id).order_by(Page.page_number, TextItem.id)).all()
                        translated = translate_texts([x.source_text for x in items], api_key, os.getenv("GEMINI_MODEL","gemini-2.5-flash"))
                        for item, result in zip(items, translated):
                            item.translated_text = result
                        db.commit()
                    st.success(f"Translated {len(translated)} text regions.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with SessionLocal() as db:
            current = db.scalars(select(TextItem).join(Page).where(Page.chapter_id == selected_id).order_by(Page.page_number, TextItem.id)).all()
            edit_data = [{"id":x.id,"page":x.page.page_number,"source_text":x.source_text,"translated_text":x.translated_text,"x":x.x,"y":x.y,"w":x.w,"h":x.h,"confidence":x.confidence} for x in current]
        if edit_data:
            edited = st.data_editor(pd.DataFrame(edit_data), use_container_width=True, hide_index=True, num_rows="fixed", disabled=["id","page","x","y","w","h","confidence"], key=f"editor_{selected_id}")
            if st.button("Save text edits"):
                with SessionLocal() as db:
                    for row in edited.to_dict("records"):
                        item = db.get(TextItem, int(row["id"]))
                        if item:
                            item.source_text = str(row.get("source_text") or "")
                            item.translated_text = str(row.get("translated_text") or "")
                    db.commit()
                st.success("Edits saved.")
                st.rerun()
        else:
            st.info("Run OCR on each page to create editable text rows. OCR may miss stylized text and sound effects.")

    with tab_export:
        st.subheader("Build translated chapter ZIP")
        st.warning("Inpainting and typesetting are best-effort. Review all pages; complex backgrounds and bubble shapes may need manual correction.")
        include_cleaned = st.checkbox("Remove detected text regions (inpainting)", value=True)
        include_typeset = st.checkbox("Draw Myanmar translations", value=True)
        if st.button("Generate ZIP"):
            out = io.BytesIO()
            with SessionLocal() as db:
                chapter = db.get(Chapter, selected_id)
                with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
                    for page in chapter.pages:
                        original = Image.open(io.BytesIO(page.image_bytes)).convert("RGB")
                        rows = [{"source_text":x.source_text,"translated_text":x.translated_text,"x":x.x,"y":x.y,"w":x.w,"h":x.h,"confidence":x.confidence} for x in page.items]
                        result = clean_text_regions(original, rows) if include_cleaned and rows else original
                        if include_typeset and rows:
                            result = typeset_text(result, rows, font_path=font_path or None)
                        zf.writestr(f"page_{page.page_number:03d}.png", image_to_png_bytes(result))
                    transcript = []
                    for page in chapter.pages:
                        for item in page.items:
                            transcript.append(f"Page {page.page_number}\nOriginal: {item.source_text}\nMyanmar: {item.translated_text}\n")
                    zf.writestr("translation.txt", "\n".join(transcript))
            st.download_button("Download translated chapter ZIP", out.getvalue(), file_name=f"chapter_{selected_id}_myanmar.zip", mime="application/zip")
