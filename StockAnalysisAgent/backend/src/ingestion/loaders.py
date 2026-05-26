"""Document loaders for PDF, DOCX, XLSX, CSV."""
import io
from pathlib import Path

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    CSVLoader,
)
import pandas as pd


def load_pdf(file_path: str | Path) -> list[Document]:
    loader = PyPDFLoader(str(file_path))
    return loader.load()


def load_docx(file_path: str | Path) -> list[Document]:
    loader = Docx2txtLoader(str(file_path))
    return loader.load()


def load_csv(file_path: str | Path, filename: str = "") -> list[Document]:
    loader = CSVLoader(file_path=str(file_path))
    docs = loader.load()
    for d in docs:
        d.metadata.setdefault("source", filename or str(file_path))
    return docs


def load_xlsx(file_path: str | Path, filename: str = "") -> list[Document]:
    dfs = pd.read_excel(file_path, sheet_name=None)
    docs = []
    for sheet_name, sheet_df in dfs.items():
        text = sheet_df.to_string(index=False)
        docs.append(
            Document(
                page_content=text,
                metadata={"source": filename or str(file_path), "sheet": sheet_name},
            )
        )
    return docs


def load_document(file_path: str | Path, filename: str | None = None) -> list[Document]:
    path = Path(file_path)
    name = filename or path.name
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return load_pdf(path)
    if suffix in (".docx", ".doc"):
        return load_docx(path)
    if suffix == ".csv":
        return load_csv(path, name)
    if suffix in (".xlsx", ".xls"):
        return load_xlsx(path, name)
    raise ValueError(f"Unsupported file type: {suffix}")
