"""Sentence-transformers embeddings via LangChain."""
from langchain_community.embeddings import HuggingFaceEmbeddings

from src.config import get_settings


def get_embeddings() -> HuggingFaceEmbeddings:
    settings = get_settings()
    return HuggingFaceEmbeddings(
        model_name=settings.embed_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
