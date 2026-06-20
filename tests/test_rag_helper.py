"""Unit tests for the RAG helper.

These tests are fully offline: they do not require a running Ollama server,
so they run reliably in CI.
"""

from pathlib import Path

import pytest
from langchain_core.documents import Document

from utils import rag_helper


def test_load_documents_reads_supported_files(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("Photosynthesis converts light to energy.")
    (tmp_path / "b.md").write_text("# Notes\nNewton's laws describe motion.")
    (tmp_path / "ignore.csv").write_text("should,be,ignored")

    docs = rag_helper.load_documents(tmp_path)

    assert len(docs) == 2
    contents = " ".join(d.page_content for d in docs)
    assert "Photosynthesis" in contents
    assert "Newton" in contents


def test_load_documents_empty_dir_returns_empty(tmp_path: Path) -> None:
    assert rag_helper.load_documents(tmp_path) == []


def test_load_documents_missing_dir_returns_empty(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist"
    assert rag_helper.load_documents(missing) == []


def test_split_documents_chunks_long_text() -> None:
    long_text = "word " * 1000  # ~5000 chars, forces multiple chunks
    docs = [Document(page_content=long_text)]

    chunks = rag_helper.split_documents(docs)

    assert len(chunks) > 1
    assert all(isinstance(c, Document) for c in chunks)
    assert all(len(c.page_content) <= 1000 for c in chunks)


def test_split_documents_short_text_single_chunk() -> None:
    docs = [Document(page_content="A short note.")]
    chunks = rag_helper.split_documents(docs)
    assert len(chunks) == 1
    assert chunks[0].page_content == "A short note."


def test_format_docs_joins_page_content() -> None:
    docs = [Document(page_content="first"), Document(page_content="second")]
    result = rag_helper._format_docs(docs)
    assert result == "first\n\nsecond"


def test_build_vectorstore_raises_when_no_documents(monkeypatch) -> None:
    # Patch load_documents so no network/embeddings call is reached.
    monkeypatch.setattr(rag_helper, "load_documents", lambda *a, **k: [])
    with pytest.raises(ValueError, match="No study material"):
        rag_helper.build_vectorstore(persist=False)


def test_summarize_notes_raises_when_no_documents(monkeypatch) -> None:
    monkeypatch.setattr(rag_helper, "load_documents", lambda *a, **k: [])
    with pytest.raises(ValueError, match="No study material"):
        rag_helper.summarize_notes()


def test_default_config_values() -> None:
    assert rag_helper.CHAT_MODEL  # non-empty
    assert rag_helper.EMBED_MODEL  # non-empty
    assert rag_helper.OLLAMA_BASE_URL.startswith("http")
    assert rag_helper.DATA_DIR.name == "data"
