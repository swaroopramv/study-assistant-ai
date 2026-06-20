"""RAG helper for the Study Assistant AI.

Handles loading study material, building a FAISS vector store, and
answering questions using a retrieval-augmented generation chain.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama, OllamaEmbeddings

load_dotenv()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
INDEX_DIR = Path(__file__).resolve().parent.parent / "faiss_index"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
CHAT_MODEL = os.getenv("CHAT_MODEL", "ministral-3:8b")
# Dedicated embedding model (the chat model does not serve embeddings).
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

PROMPT = ChatPromptTemplate.from_template(
    """You are a helpful study assistant. Use ONLY the context below to answer
the question. If the answer is not in the context, say you don't know based on
the provided notes. Be clear and concise, and explain concepts simply.

Context:
{context}

Question: {question}

Answer:"""
)


def _get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(model=EMBED_MODEL, base_url=OLLAMA_BASE_URL)


def _get_llm(temperature: float = 0.2) -> ChatOllama:
    return ChatOllama(
        model=CHAT_MODEL, base_url=OLLAMA_BASE_URL, temperature=temperature
    )


def load_documents(data_dir: Path = DATA_DIR) -> list[Document]:
    """Load all .txt, .md, and .pdf files from the data directory."""
    docs: list[Document] = []
    if not data_dir.exists():
        return docs
    for path in data_dir.rglob("*"):
        if path.suffix.lower() in {".txt", ".md"}:
            docs.extend(TextLoader(str(path), encoding="utf-8").load())
        elif path.suffix.lower() == ".pdf":
            docs.extend(PyPDFLoader(str(path)).load())
    return docs


def split_documents(docs: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=150, separators=["\n\n", "\n", ". ", " ", ""]
    )
    return splitter.split_documents(docs)


def build_vectorstore(persist: bool = True) -> FAISS:
    """Build a FAISS vector store from the documents in the data directory."""
    docs = load_documents()
    if not docs:
        raise ValueError(
            f"No study material found in {DATA_DIR}. Add .txt, .md, or .pdf files."
        )
    chunks = split_documents(docs)
    embeddings = _get_embeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    if persist:
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        vectorstore.save_local(str(INDEX_DIR))
    return vectorstore


def load_vectorstore() -> FAISS:
    """Load a persisted FAISS index, building it if it doesn't exist."""
    embeddings = _get_embeddings()
    if INDEX_DIR.exists():
        return FAISS.load_local(
            str(INDEX_DIR), embeddings, allow_dangerous_deserialization=True
        )
    return build_vectorstore()


def _format_docs(docs: list[Document]) -> str:
    return "\n\n".join(d.page_content for d in docs)


def build_qa_chain(vectorstore: FAISS, k: int = 4):
    """Build a retrieval-augmented QA chain."""
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    llm = _get_llm(temperature=0.2)
    chain = (
        {"context": retriever | _format_docs, "question": RunnablePassthrough()}
        | PROMPT
        | llm
        | StrOutputParser()
    )
    return chain


def answer_question(question: str, k: int = 4) -> str:
    """Convenience one-shot helper to answer a question against the notes."""
    vectorstore = load_vectorstore()
    chain = build_qa_chain(vectorstore, k=k)
    return chain.invoke(question)


def summarize_notes() -> str:
    """Summarize all loaded study material."""
    docs = load_documents()
    if not docs:
        raise ValueError(f"No study material found in {DATA_DIR}.")
    text = "\n\n".join(d.page_content for d in docs)[:12000]
    llm = _get_llm(temperature=0.3)
    prompt = ChatPromptTemplate.from_template(
        "Summarize the following study notes into clear bullet points grouped by "
        "topic. Highlight key concepts and definitions.\n\nNotes:\n{notes}"
    )
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"notes": text})
