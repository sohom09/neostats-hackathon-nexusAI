import os
from typing import List
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

FAISS_INDEX_PATH = "faiss_index"
EMBEDDING_MODEL  = "BAAI/bge-small-en-v1.5"


class RAGManager:
    def __init__(self, index_path: str = FAISS_INDEX_PATH):
        self.index_path       = index_path
        self.embeddings       = None
        self.vector_store     = None
        self.loaded_documents: List[str] = []
        self._init_embeddings()
        self._load_existing_index()

    def _init_embeddings(self):
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
            print("[RAG] Embeddings loaded: " + EMBEDDING_MODEL)
        except Exception as exc:
            print("[RAG] Failed to load embeddings: " + str(exc).encode('ascii', 'replace').decode('ascii'))

    def _load_existing_index(self):
        if os.path.exists(self.index_path) and self.embeddings:
            try:
                self.vector_store = FAISS.load_local(
                    self.index_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
                print("[RAG] FAISS index loaded from disk.")
            except Exception as exc:
                print("[RAG] Could not load index: " + str(exc).encode('ascii', 'replace').decode('ascii'))

    def add_documents(self, file_path: str, display_name: str = "") -> bool:
        if not self.embeddings:
            return False
        name = display_name or os.path.basename(file_path)
        try:
            ext = os.path.splitext(file_path)[1].lower()
            loader = PyPDFLoader(file_path) if ext == ".pdf" else TextLoader(file_path, encoding="utf-8")
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = name
            splitter = RecursiveCharacterTextSplitter(chunk_size=256, chunk_overlap=20)
            chunks = splitter.split_documents(docs)
            print("[RAG] " + name + ": " + str(len(chunks)) + " chunks")
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(chunks, self.embeddings)
            else:
                self.vector_store.add_documents(chunks)
            self.vector_store.save_local(self.index_path)
            self.loaded_documents.append(name)
            return True
        except Exception as exc:
            print("[RAG] Error: " + str(exc).encode('ascii', 'replace').decode('ascii'))
            return False

    def search(self, query: str, k: int = 4) -> List[Document]:
        if not self.vector_store:
            return []
        try:
            return self.vector_store.similarity_search(query, k=k)
        except Exception:
            return []

    def is_ready(self) -> bool:
        return self.vector_store is not None

    def get_loaded_documents(self) -> List[str]:
        return self.loaded_documents
