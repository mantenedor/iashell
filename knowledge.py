#!/usr/bin/env python3
import csv
import hashlib
import json
import mimetypes
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook
from PIL import Image
from PyPDF2 import PdfReader

KNOWLEDGE_DIR = Path("/data/ia/knowledge")
DOCS_RAW_DIR = KNOWLEDGE_DIR / "raw"
DOCS_PARSED_DIR = KNOWLEDGE_DIR / "parsed"
DOCS_INDEX_FILE = KNOWLEDGE_DIR / "index.json"
CHUNKS_FILE = KNOWLEDGE_DIR / "chunks.jsonl"

TEXT_EXTENSIONS = {".txt", ".md", ".log", ".json", ".yaml", ".yml", ".ini", ".cfg"}
CSV_EXTENSIONS = {".csv", ".tsv"}
SPREADSHEET_EXTENSIONS = {".xlsx", ".xlsm"}
PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}


def ensure_knowledge_structure():
    DOCS_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_PARSED_DIR.mkdir(parents=True, exist_ok=True)

    if not DOCS_INDEX_FILE.exists():
        DOCS_INDEX_FILE.write_text("[]\n", encoding="utf-8")

    if not CHUNKS_FILE.exists():
        CHUNKS_FILE.write_text("", encoding="utf-8")


def now_iso():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^\w\s.-]", "-", value, flags=re.UNICODE)
    value = re.sub(r"[\s/]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-._") or "documento"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_index():
    ensure_knowledge_structure()
    with open(DOCS_INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_index(index_data):
    with open(DOCS_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)


def detect_doc_type(path: Path) -> str:
    ext = path.suffix.lower()

    if ext in TEXT_EXTENSIONS:
        return "text"
    if ext in CSV_EXTENSIONS:
        return "csv"
    if ext in SPREADSHEET_EXTENSIONS:
        return "spreadsheet"
    if ext in PDF_EXTENSIONS:
        return "pdf"
    if ext in IMAGE_EXTENSIONS:
        return "image"

    mime, _ = mimetypes.guess_type(str(path))
    if mime and mime.startswith("text/"):
        return "text"

    return "binary"


def make_doc_id(path: Path, file_hash: str) -> str:
    return f"{slugify(path.stem)}-{file_hash[:12]}"


def read_text_file(path: Path) -> str:
    encodings = ["utf-8", "utf-8-sig", "latin-1"]
    for enc in encodings:
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def parse_text_document(doc_meta: dict) -> dict:
    raw_path = Path(doc_meta["path_raw"])
    text = read_text_file(raw_path)

    return {
        "doc_id": doc_meta["doc_id"],
        "type": "text",
        "title": raw_path.name,
        "sections": [
            {
                "section": "body",
                "text": text
            }
        ]
    }


def parse_csv_document(doc_meta: dict) -> dict:
    raw_path = Path(doc_meta["path_raw"])
    ext = raw_path.suffix.lower()
    delimiter = "\t" if ext == ".tsv" else ","

    rows = []
    with open(raw_path, "r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            rows.append(row)

    preview_text = "\n".join([" | ".join(map(str, row)) for row in rows[:200]])

    return {
        "doc_id": doc_meta["doc_id"],
        "type": "csv",
        "title": raw_path.name,
        "tables": [
            {
                "name": raw_path.stem,
                "rows": rows[:2000],
                "preview_text": preview_text
            }
        ]
    }


def parse_spreadsheet_document(doc_meta: dict) -> dict:
    raw_path = Path(doc_meta["path_raw"])
    wb = load_workbook(raw_path, data_only=True, read_only=True)

    sheets = []
    for ws in wb.worksheets:
        rows = []
        row_limit = 300
        col_limit = 30

        for row_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if row_idx > row_limit:
                break
            normalized = []
            for cell in list(row)[:col_limit]:
                if cell is None:
                    normalized.append("")
                else:
                    normalized.append(str(cell))
            rows.append(normalized)

        preview_lines = []
        for row in rows[:80]:
            if any(x.strip() for x in row):
                preview_lines.append(" | ".join(row))

        sheets.append({
            "name": ws.title,
            "rows": rows,
            "preview_text": "\n".join(preview_lines)
        })

    wb.close()

    return {
        "doc_id": doc_meta["doc_id"],
        "type": "spreadsheet",
        "title": raw_path.name,
        "sheets": sheets
    }


def parse_pdf_document(doc_meta: dict) -> dict:
    raw_path = Path(doc_meta["path_raw"])
    reader = PdfReader(str(raw_path))

    pages = []
    for idx, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""

        pages.append({
            "page": idx,
            "text": text
        })

    return {
        "doc_id": doc_meta["doc_id"],
        "type": "pdf",
        "title": raw_path.name,
        "pages": pages
    }


def parse_image_document(doc_meta: dict) -> dict:
    raw_path = Path(doc_meta["path_raw"])

    width = None
    height = None
    mode = None
    try:
        with Image.open(raw_path) as img:
            width, height = img.size
            mode = img.mode
    except Exception:
        pass

    sidecar_txt = raw_path.with_suffix(raw_path.suffix + ".txt")
    sidecar_md = raw_path.with_suffix(raw_path.suffix + ".md")

    description = ""
    if sidecar_txt.exists():
        description = read_text_file(sidecar_txt).strip()
    elif sidecar_md.exists():
        description = read_text_file(sidecar_md).strip()

    return {
        "doc_id": doc_meta["doc_id"],
        "type": "image",
        "title": raw_path.name,
        "image_meta": {
            "width": width,
            "height": height,
            "mode": mode
        },
        "description": description
    }


def parse_document(doc_meta: dict) -> dict:
    doc_type = doc_meta["type"]

    if doc_type == "text":
        return parse_text_document(doc_meta)
    if doc_type == "csv":
        return parse_csv_document(doc_meta)
    if doc_type == "spreadsheet":
        return parse_spreadsheet_document(doc_meta)
    if doc_type == "pdf":
        return parse_pdf_document(doc_meta)
    if doc_type == "image":
        return parse_image_document(doc_meta)

    return {
        "doc_id": doc_meta["doc_id"],
        "type": doc_type,
        "title": Path(doc_meta["path_raw"]).name,
        "unsupported": True
    }


def save_parsed_document(parsed_doc: dict, parsed_path: Path):
    with open(parsed_path, "w", encoding="utf-8") as f:
        json.dump(parsed_doc, f, ensure_ascii=False, indent=2)


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def split_text_into_chunks(text: str, max_chars: int = 1800, overlap: int = 250):
    text = normalize_whitespace(text)
    if not text:
        return []

    parts = []
    start = 0
    size = len(text)

    while start < size:
        end = min(start + max_chars, size)
        chunk = text[start:end].strip()
        if chunk:
            parts.append(chunk)
        if end >= size:
            break
        start = max(end - overlap, 0)

    return parts


def chunk_document(parsed_doc: dict):
    doc_id = parsed_doc["doc_id"]
    doc_type = parsed_doc["type"]
    title = parsed_doc.get("title", doc_id)
    chunks = []

    def add_chunk(text: str, source_ref: str, extra=None):
        extra = extra or {}
        for idx, part in enumerate(split_text_into_chunks(text), start=1):
            chunk_id = f"{doc_id}::{source_ref}::{idx:03d}"
            chunk = {
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "type": doc_type,
                "title": title,
                "source_ref": source_ref,
                "text": part,
                "keywords": extract_keywords(title + "\n" + part)
            }
            chunk.update(extra)
            chunks.append(chunk)

    if doc_type == "text":
        for section in parsed_doc.get("sections", []):
            add_chunk(section.get("text", ""), f"section:{section.get('section', 'body')}")

    elif doc_type == "csv":
        for table in parsed_doc.get("tables", []):
            add_chunk(
                table.get("preview_text", ""),
                f"table:{table.get('name', 'default')}"
            )

    elif doc_type == "spreadsheet":
        for sheet in parsed_doc.get("sheets", []):
            add_chunk(
                sheet.get("preview_text", ""),
                f"sheet:{sheet.get('name', 'Sheet1')}",
                {"sheet": sheet.get("name", "Sheet1")}
            )

    elif doc_type == "pdf":
        for page in parsed_doc.get("pages", []):
            add_chunk(
                page.get("text", ""),
                f"page:{page.get('page', 1)}",
                {"page": page.get("page", 1)}
            )

    elif doc_type == "image":
        description = parsed_doc.get("description", "")
        meta = parsed_doc.get("image_meta", {})
        text = f"Imagem: {title}\nDescrição: {description}\nMetadados: {meta}"
        add_chunk(text, "image:description")

    return chunks


def extract_keywords(text: str):
    words = re.findall(r"[a-zA-Z0-9_./:-]{3,}", text.lower())
    stop = {
        "the", "and", "for", "with", "that", "this", "from", "como", "para",
        "uma", "com", "sem", "dos", "das", "que", "por", "não", "ser", "são",
        "eow", "json", "text", "page", "sheet"
    }
    keywords = []
    seen = set()
    for w in words:
        if w in stop:
            continue
        if w not in seen:
            seen.add(w)
            keywords.append(w)
    return keywords[:80]


def rewrite_chunks_for_doc(doc_id: str, new_chunks: list):
    ensure_knowledge_structure()

    existing = []
    if CHUNKS_FILE.exists():
        with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if obj.get("doc_id") != doc_id:
                    existing.append(obj)

    existing.extend(new_chunks)

    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        for item in existing:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def ingest_file(path: str) -> dict:
    ensure_knowledge_structure()

    src = Path(path)
    if not src.exists() or not src.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {src}")

    file_hash = sha256_file(src)
    doc_id = make_doc_id(src, file_hash)
    doc_type = detect_doc_type(src)

    raw_filename = f"{doc_id}{src.suffix.lower()}"
    raw_path = DOCS_RAW_DIR / raw_filename
    parsed_path = DOCS_PARSED_DIR / f"{doc_id}.json"

    if not raw_path.exists():
        shutil.copy2(src, raw_path)

    index_data = load_index()

    existing = next((x for x in index_data if x.get("doc_id") == doc_id), None)
    if existing:
        return existing

    meta = {
        "doc_id": doc_id,
        "filename_original": src.name,
        "filename_raw": raw_filename,
        "path_raw": str(raw_path),
        "path_parsed": str(parsed_path),
        "type": doc_type,
        "hash_sha256": file_hash,
        "created_at": now_iso(),
        "status": "ingested"
    }

    index_data.append(meta)
    save_index(index_data)
    return meta


def reindex_document(doc_id: str) -> dict:
    index_data = load_index()
    meta = next((x for x in index_data if x.get("doc_id") == doc_id), None)
    if not meta:
        raise ValueError(f"Documento não encontrado no índice: {doc_id}")

    parsed_doc = parse_document(meta)
    save_parsed_document(parsed_doc, Path(meta["path_parsed"]))
    chunks = chunk_document(parsed_doc)
    rewrite_chunks_for_doc(doc_id, chunks)

    meta["status"] = "parsed"
    meta["parsed_at"] = now_iso()
    meta["chunk_count"] = len(chunks)
    save_index(index_data)

    return meta


def ingest_and_index(path: str) -> dict:
    meta = ingest_file(path)
    return reindex_document(meta["doc_id"])


def list_documents():
    return load_index()


def load_all_chunks():
    ensure_knowledge_structure()
    items = []
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def score_chunk(query_terms: set, chunk: dict) -> int:
    haystack = (
        chunk.get("title", "").lower() + "\n" +
        chunk.get("text", "").lower() + "\n" +
        " ".join(chunk.get("keywords", []))
    )

    score = 0
    for term in query_terms:
        if term in haystack:
            score += 5
        if term in chunk.get("title", "").lower():
            score += 3
        if term in " ".join(chunk.get("keywords", [])):
            score += 2
    return score


def search_chunks(query: str, limit: int = 5):
    query_terms = set(re.findall(r"[a-zA-Z0-9_./:-]{2,}", query.lower()))
    if not query_terms:
        return []

    chunks = load_all_chunks()
    scored = []

    for chunk in chunks:
        score = score_chunk(query_terms, chunk)
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:limit]]


def build_context_block(query: str, limit: int = 5) -> str:
    hits = search_chunks(query, limit=limit)
    if not hits:
        return ""

    parts = []
    for hit in hits:
        label = f"{hit.get('doc_id')} | {hit.get('source_ref')}"
        parts.append(f"[{label}]\n{hit.get('text', '')}")

    return "\n\n".join(parts)
