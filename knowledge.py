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

from dotenv import load_dotenv
from openpyxl import load_workbook
from PIL import Image
from PyPDF2 import PdfReader


def load_local_env():
    env_file = Path(os.environ.get("IA_ENV_FILE", "conf/.env"))
    if env_file.exists():
        load_dotenv(env_file)


load_local_env()

TMP_DIR = Path(os.environ["TMP_DIR"])
TMP_RAW_DIR = Path(os.environ["TMP_RAW_DIR"])
KNOWLEDGE_DIR = Path(os.environ["KNOWLEDGE_DIR"])
KNOWLEDGE_RAW_DIR = Path(os.environ["KNOWLEDGE_RAW_DIR"])
PARSED_DIR = Path(os.environ["PARSED_DIR"])
DOCS_INDEX_FILE = Path(os.environ["DOCS_INDEX_FILE"])
CHUNKS_FILE = Path(os.environ["CHUNKS_FILE"])


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


def ensure_runtime_structure():
    ensure_dir(TMP_DIR)
    ensure_dir(TMP_RAW_DIR)
    ensure_dir(KNOWLEDGE_DIR)
    ensure_dir(KNOWLEDGE_RAW_DIR)
    ensure_dir(PARSED_DIR)

    ensure_parent(DOCS_INDEX_FILE)
    ensure_parent(CHUNKS_FILE)

    if not DOCS_INDEX_FILE.exists():
        DOCS_INDEX_FILE.write_text("[]\n", encoding="utf-8")

    if not CHUNKS_FILE.exists():
        CHUNKS_FILE.write_text("", encoding="utf-8")


def sha256_file(path: Path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_size(path: Path):
    return path.stat().st_size


def now_iso():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def slugify(value):
    value = value.lower().strip()
    value = re.sub(r"[^\w\s.-]", "-", value)
    value = re.sub(r"\s+", "-", value)
    return value.strip("-._")


def load_index():
    ensure_runtime_structure()
    with open(DOCS_INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_index(index_data):
    ensure_parent(DOCS_INDEX_FILE)
    with open(DOCS_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)


def list_documents():
    return load_index()


def rewrite_chunks_for_doc(doc_id: str, new_chunks: list):
    ensure_runtime_structure()

    remaining_chunks = []

    if CHUNKS_FILE.exists():
        with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if obj.get("doc_id") != doc_id:
                    remaining_chunks.append(obj)

    remaining_chunks.extend(new_chunks)

    ensure_parent(CHUNKS_FILE)

    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        for item in remaining_chunks:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def detect_doc_type(path: Path):
    ext = path.suffix.lower()

    if ext in {".txt", ".md", ".log", ".json", ".yaml", ".yml", ".ini", ".cfg"}:
        return "text"

    if ext in {".csv", ".tsv"}:
        return "csv"

    if ext in {".xlsx", ".xlsm"}:
        return "spreadsheet"

    if ext in {".pdf"}:
        return "pdf"

    if ext in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}:
        return "image"

    mime, _ = mimetypes.guess_type(str(path))
    if mime and mime.startswith("text/"):
        return "text"

    return "binary"


def make_doc_id(path: Path, file_hash: str):
    return f"{slugify(path.stem)}-{file_hash[:12]}"


def read_text_file(path: Path):
    encodings = ["utf-8", "utf-8-sig", "latin-1"]
    for enc in encodings:
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def summarize_text(text: str, limit: int = 400) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    return text[:limit].rstrip() + ("..." if len(text) > limit else "")


def parse_pdf(path: Path):
    reader = PdfReader(str(path))
    pages = []

    for page_num, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        pages.append({"page": page_num, "text": text})

    return pages


def parse_spreadsheet(path: Path):
    wb = load_workbook(path, data_only=True, read_only=True)
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
                normalized.append("" if cell is None else str(cell))
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
    return sheets


def parse_csv(path: Path):
    ext = path.suffix.lower()
    delimiter = "\t" if ext == ".tsv" else ","

    rows = []
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            rows.append(row)

    preview_text = "\n".join([" | ".join(map(str, row)) for row in rows[:200]])
    return {
        "name": path.stem,
        "rows": rows[:2000],
        "preview_text": preview_text
    }


def parse_image(path: Path):
    width = None
    height = None
    mode = None
    try:
        with Image.open(path) as img:
            width, height = img.size
            mode = img.mode
    except Exception:
        pass

    sidecar_txt = path.with_suffix(path.suffix + ".txt")
    sidecar_md = path.with_suffix(path.suffix + ".md")

    description = ""
    if sidecar_txt.exists():
        description = read_text_file(sidecar_txt).strip()
    elif sidecar_md.exists():
        description = read_text_file(sidecar_md).strip()

    return {
        "width": width,
        "height": height,
        "mode": mode,
        "description": description,
    }


def parse_document(meta):
    raw_path = Path(meta["path_raw"])
    doc_type = meta["type"]

    if doc_type == "text":
        return {
            "doc_id": meta["doc_id"],
            "type": "text",
            "title": raw_path.name,
            "sections": [{"section": "body", "text": read_text_file(raw_path)}],
        }

    if doc_type == "pdf":
        return {
            "doc_id": meta["doc_id"],
            "type": "pdf",
            "title": raw_path.name,
            "pages": parse_pdf(raw_path),
        }

    if doc_type == "csv":
        return {
            "doc_id": meta["doc_id"],
            "type": "csv",
            "title": raw_path.name,
            "tables": [parse_csv(raw_path)],
        }

    if doc_type == "spreadsheet":
        return {
            "doc_id": meta["doc_id"],
            "type": "spreadsheet",
            "title": raw_path.name,
            "sheets": parse_spreadsheet(raw_path),
        }

    if doc_type == "image":
        image_meta = parse_image(raw_path)
        return {
            "doc_id": meta["doc_id"],
            "type": "image",
            "title": raw_path.name,
            "image_meta": {
                "width": image_meta["width"],
                "height": image_meta["height"],
                "mode": image_meta["mode"],
            },
            "description": image_meta["description"],
        }

    return {
        "doc_id": meta["doc_id"],
        "type": doc_type,
        "title": raw_path.name,
        "unsupported": True,
    }


def save_parsed_document(parsed_doc: dict, parsed_path: Path):
    ensure_parent(parsed_path)
    with open(parsed_path, "w", encoding="utf-8") as f:
        json.dump(parsed_doc, f, ensure_ascii=False, indent=2)


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def split_chunks(text, size=1800, overlap=250):
    text = normalize_whitespace(text)
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, 0)
    return chunks


def extract_keywords(text: str):
    words = re.findall(r"[a-zA-Z0-9_./:-]{3,}", text.lower())
    stop = {
        "the", "and", "for", "with", "that", "this", "from", "como", "para",
        "uma", "com", "sem", "dos", "das", "que", "por", "não", "ser", "são",
        "json", "text", "page", "sheet",
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


def chunk_document(parsed_doc):
    doc_id = parsed_doc["doc_id"]
    doc_type = parsed_doc["type"]
    title = parsed_doc.get("title", doc_id)
    chunks = []

    def add_chunk(text: str, source_ref: str, extra=None):
        extra = extra or {}
        for idx, part in enumerate(split_chunks(text), start=1):
            chunk = {
                "doc_id": doc_id,
                "chunk_id": f"{doc_id}::{source_ref}::{idx:03d}",
                "title": title,
                "type": doc_type,
                "source_ref": source_ref,
                "text": part,
                "keywords": extract_keywords(title + "\n" + part),
            }
            chunk.update(extra)
            chunks.append(chunk)

    if doc_type == "text":
        for section in parsed_doc.get("sections", []):
            add_chunk(section.get("text", ""), f"section:{section.get('section', 'body')}")

    elif doc_type == "pdf":
        for page in parsed_doc.get("pages", []):
            add_chunk(page.get("text", ""), f"page:{page.get('page', 1)}", {"page": page.get("page", 1)})

    elif doc_type == "csv":
        for table in parsed_doc.get("tables", []):
            add_chunk(table.get("preview_text", ""), f"table:{table.get('name', 'default')}")

    elif doc_type == "spreadsheet":
        for sheet in parsed_doc.get("sheets", []):
            add_chunk(
                sheet.get("preview_text", ""),
                f"sheet:{sheet.get('name', 'Sheet1')}",
                {"sheet": sheet.get("name", "Sheet1")}
            )

    elif doc_type == "image":
        text = f"Imagem: {title}\nDescrição: {parsed_doc.get('description', '')}\nMetadados: {parsed_doc.get('image_meta', {})}"
        add_chunk(text, "image:description")

    return chunks


def build_summary_from_parsed(parsed_doc: dict) -> str:
    doc_type = parsed_doc.get("type")

    if doc_type == "pdf":
        text = "\n".join(p.get("text", "") for p in parsed_doc.get("pages", [])[:3])
        return summarize_text(text)

    if doc_type == "text":
        text = "\n".join(s.get("text", "") for s in parsed_doc.get("sections", []))
        return summarize_text(text)

    if doc_type == "csv":
        text = "\n".join(t.get("preview_text", "") for t in parsed_doc.get("tables", []))
        return summarize_text(text)

    if doc_type == "spreadsheet":
        text = "\n".join(s.get("preview_text", "") for s in parsed_doc.get("sheets", [])[:3])
        return summarize_text(text)

    if doc_type == "image":
        return summarize_text(parsed_doc.get("description", "") or f"Imagem {parsed_doc.get('title', '')}")

    return ""


def pick_raw_dir(source_mode: str) -> Path:
    if source_mode == "tmp":
        return TMP_RAW_DIR
    return KNOWLEDGE_RAW_DIR


def ingest_file(path: str, source_mode="manual"):
    ensure_runtime_structure()

    src = Path(path)
    if not src.exists() or not src.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {src}")

    file_hash = sha256_file(src)
    doc_id = make_doc_id(src, file_hash)
    doc_type = detect_doc_type(src)

    raw_root = pick_raw_dir(source_mode)
    raw_filename = f"{doc_id}{src.suffix.lower()}"
    raw_path = raw_root / raw_filename
    parsed_path = PARSED_DIR / f"{doc_id}.json"

    ensure_dir(raw_root)

    index_data = load_index()
    existing = next((x for x in index_data if x.get("doc_id") == doc_id), None)
    if existing:
        return existing

    if not raw_path.exists():
        shutil.copy2(src, raw_path)

    meta = {
        "doc_id": doc_id,
        "filename_original": src.name,
        "filename_raw": raw_filename,
        "path_source": str(src.resolve()),
        "path_raw": str(raw_path),
        "path_parsed": str(parsed_path),
        "type": doc_type,
        "hash_sha256": file_hash,
        "size_bytes": file_size(src),
        "created_at": now_iso(),
        "status": "ingested",
        "source_mode": source_mode,
        "summary": "",
    }

    index_data.append(meta)
    save_index(index_data)
    return meta


def reindex_document(doc_id):
    index_data = load_index()
    meta = next(x for x in index_data if x["doc_id"] == doc_id)

    parsed_doc = parse_document(meta)
    save_parsed_document(parsed_doc, Path(meta["path_parsed"]))

    chunks = chunk_document(parsed_doc)
    rewrite_chunks_for_doc(doc_id, chunks)

    meta["chunk_count"] = len(chunks)
    meta["parsed_at"] = now_iso()
    meta["status"] = "parsed"
    meta["summary"] = build_summary_from_parsed(parsed_doc)

    save_index(index_data)
    return meta


def ingest_and_index(path, source_mode="manual"):
    meta = ingest_file(path, source_mode)
    return reindex_document(meta["doc_id"])


def upsert_document(path: str, source_mode: str):
    ensure_runtime_structure()

    src = Path(path)
    if not src.exists() or not src.is_file():
        return None

    current_hash = sha256_file(src)
    index_data = load_index()

    existing = next(
        (x for x in index_data if x.get("path_source") == str(src.resolve())),
        None
    )

    if existing and existing.get("hash_sha256") == current_hash:
        return None

    if existing:
        old_doc_id = existing["doc_id"]
        index_data = [x for x in index_data if x.get("doc_id") != old_doc_id]
        save_index(index_data)
        rewrite_chunks_for_doc(old_doc_id, [])

        old_parsed = Path(existing.get("path_parsed", ""))
        if old_parsed.exists():
            old_parsed.unlink()

    return ingest_and_index(str(src), source_mode)


def sync_directory(source_dir: Path, source_mode: str):
    ensure_runtime_structure()
    changed = []

    for item in sorted(source_dir.iterdir()):
        if item.name.startswith("."):
            continue
        if not item.is_file():
            continue

        result = upsert_document(str(item), source_mode)
        if result is not None:
            changed.append(result)

    return changed


def sync_all_sources():
    changed = []
    changed.extend(sync_directory(TMP_DIR, "tmp"))
    changed.extend(sync_directory(KNOWLEDGE_DIR, "knowledge"))
    return changed


def load_all_chunks():
    ensure_runtime_structure()
    chunks = []

    if CHUNKS_FILE.exists():
        with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    chunks.append(json.loads(line))

    return chunks


def get_document_chunks(doc_id: str):
    return [c for c in load_all_chunks() if c.get("doc_id") == doc_id]


def build_doc_context(doc_id: str, limit: int = 8):
    chunks = get_document_chunks(doc_id)[:limit]

    parts = []
    for c in chunks:
        label = f"{c.get('doc_id', '')} | {c.get('source_ref', '')}"
        parts.append(f"[{label}]\n{c.get('text', '')}")

    return "\n\n".join(parts)


def format_document_catalog(limit: int = 50):
    docs = load_index()
    docs = sorted(docs, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]

    if not docs:
        return ""

    parts = []
    for d in docs:
        parts.append(
            "\n".join([
                f"doc_id: {d.get('doc_id', '')}",
                f"nome: {d.get('filename_original', '')}",
                f"tipo: {d.get('type', '')}",
                f"origem: {d.get('source_mode', '')}",
                f"caminho: {d.get('path_source', '')}",
                f"tamanho_bytes: {d.get('size_bytes', 0)}",
                f"resumo: {d.get('summary', '')}",
            ])
        )

    return "\n\n".join(parts)


def search_chunks(query, limit=5):
    query_terms = set(re.findall(r"[a-zA-Z0-9_./:-]{2,}", query.lower()))
    if not query_terms:
        return []

    results = []
    for chunk in load_all_chunks():
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

        if score > 0:
            results.append((score, chunk))

    results.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in results[:limit]]


def build_context_block(query, limit=5):
    hits = search_chunks(query, limit)

    parts = []
    for h in hits:
        label = f"{h.get('doc_id', '')} | {h.get('source_ref', '')}"
        parts.append(f"[{label}]\n{h.get('text', '')}")

    return "\n\n".join(parts)
