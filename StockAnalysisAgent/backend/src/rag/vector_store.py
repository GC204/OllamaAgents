"""ChromaDB vector store with persistence."""
from pathlib import Path

from langchain_community.vectorstores import Chroma

from src.config import get_settings
from src.rag.embeddings import get_embeddings


def get_vector_store():
    settings = get_settings()
    Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name="financial_docs",
        embedding_function=get_embeddings(),
        persist_directory=settings.chroma_persist_dir,
    )


def get_retriever(top_k: int | None = None):
    settings = get_settings()
    vs = get_vector_store()
    return vs.as_retriever(search_kwargs={"k": top_k or settings.rag_top_k})
