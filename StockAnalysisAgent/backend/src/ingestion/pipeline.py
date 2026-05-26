"""Ingest documents: load -> chunk -> embed -> add to vector store."""
from pathlib import Path

from src.config import get_settings, ensure_dirs
from src.rag import get_vector_store, get_text_splitter


def ingest_file(file_path: str | Path, filename: str | None = None) -> dict:
    """Load a file, chunk, embed, and add to vector store. Returns summary."""
    from src.ingestion.loaders import load_document

    ensure_dirs(get_settings())
    path = Path(file_path)
    name = filename or path.name

    docs = load_document(path, name)
    if not docs:
        return {"ok": False, "message": "No content extracted", "chunks": 0}

    splitter = get_text_splitter()
    chunks = splitter.split_documents(docs)
    for c in chunks:
        c.metadata.setdefault("filename", name)

    vector_store = get_vector_store()
    vector_store.add_documents(chunks)

    return {"ok": True, "message": f"Ingested {name}", "chunks": len(chunks), "filename": name}
