import os
import shutil
import logging
import math
import ollama
from typing import Dict, List
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.embeddings import Embeddings

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

BASE_DIR = os.getcwd()
if os.path.exists(os.path.join(BASE_DIR, "data")):
    DATA_ROOT = os.path.join(BASE_DIR, "data")
elif os.path.exists(os.path.join(BASE_DIR, "..", "data")):
    DATA_ROOT = os.path.join(BASE_DIR, "..", "data")
else:
    DATA_ROOT = "data"

DATA_RAW_DIR       = os.path.join(DATA_ROOT, "raw")
DATA_PROCESSED_DIR = os.path.join(DATA_ROOT, "processed")
FAISS_INDEX_PATH   = os.path.join(DATA_ROOT, "processed", "faiss_index")

# ✅ Correct models for your setup
EMBEDDING_MODEL   = "nomic-embed-text:latest"
GENERATION_MODEL  = "llama3.1:8b"


class OllamaEmbeddings(Embeddings):
    """Ollama embeddings using nomic-embed-text."""

    def __init__(self, model: str = EMBEDDING_MODEL):
        self.model = model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            # ✅ Correct API for Ollama 0.19.0
            resp = ollama.embeddings(model=self.model, prompt=text)
            embeddings.append(resp["embedding"])
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        # ✅ Correct API for Ollama 0.19.0
        resp = ollama.embeddings(model=self.model, prompt=text)
        return resp["embedding"]


def _load_file(file_path: str, filename: str) -> list:
    """Load a file based on extension — supports pdf, txt, md."""
    ext = filename.lower().rsplit(".", 1)[-1]
    try:
        if ext == "pdf":
            return PyPDFLoader(file_path).load()
        elif ext in ("txt", "md"):      # ✅ .md files now supported
            return TextLoader(file_path, encoding="utf-8").load()
        else:
            logging.warning(f"Unsupported file type skipped: {filename}")
            return []
    except Exception as e:
        logging.error(f"Failed to load {filename}: {e}")
        return []


def ingest_documents():
    """Ingest raw documents into the FAISS vector index."""
    os.makedirs(DATA_RAW_DIR,       exist_ok=True)
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)

    files = [
        f for f in os.listdir(DATA_RAW_DIR)
        if os.path.isfile(os.path.join(DATA_RAW_DIR, f))
    ]

    if not files:
        logging.info("No new documents to ingest.")
        return

    logging.info(f"Found {len(files)} document(s). Starting ingestion...")

    documents = []
    for f in files:
        loaded = _load_file(os.path.join(DATA_RAW_DIR, f), f)
        documents.extend(loaded)
        logging.info(f"  '{f}' → {len(loaded)} section(s) loaded")

    if not documents:
        logging.warning("No valid content extracted.")
        return

    # ✅ Smaller chunks = more precise retrieval
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    docs = splitter.split_documents(documents)
    logging.info(f"Split into {len(docs)} chunk(s).")

    embeddings = OllamaEmbeddings()

    if os.path.exists(FAISS_INDEX_PATH):
        try:
            db = FAISS.load_local(
                FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True
            )
            db.add_documents(docs)
            logging.info("Updated existing FAISS index.")
        except Exception as e:
            logging.error(f"Could not load existing index ({e}), rebuilding...")
            db = FAISS.from_documents(docs, embeddings)
    else:
        db = FAISS.from_documents(docs, embeddings)
        logging.info("Created new FAISS index.")

    db.save_local(FAISS_INDEX_PATH)

    for f in files:
        try:
            shutil.move(
                os.path.join(DATA_RAW_DIR, f),
                os.path.join(DATA_PROCESSED_DIR, f)
            )
        except Exception as e:
            logging.error(f"Failed to move '{f}': {e}")

    logging.info("✅ Ingestion complete.")


def get_relevant_context(query: str, k: int = 4) -> Dict:
    """Retrieve relevant chunks from FAISS for a given query."""
    if not os.path.exists(FAISS_INDEX_PATH):
        return {
            "context_text": "",
            "kb_context_found": False,
            "retrieval_score": 0.0,
            "matches": [],
        }

    embeddings = OllamaEmbeddings()
    try:
        db = FAISS.load_local(
            FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True
        )
        docs_with_scores = db.similarity_search_with_score(query, k=k)

        matches: List[Dict] = []
        for doc, distance in docs_with_scores:
            # ✅ exp decay: distance ~0 → score ~1.0, distance ~10 → score ~0.6
            similarity_score = round(max(0.0, min(1.0, math.exp(-distance / 10.0))), 4)
            matches.append({
                "content":          doc.page_content,
                "metadata":         doc.metadata,
                "distance":         round(float(distance), 4),
                "similarity_score": similarity_score,
            })

        # ✅ Drop very poor matches
        matches = [m for m in matches if m["similarity_score"] > 0.1]

        context_text    = "\n\n---\n\n".join(m["content"] for m in matches)
        retrieval_score = (
            sum(m["similarity_score"] for m in matches) / len(matches)
            if matches else 0.0
        )

        return {
            "context_text":     context_text,
            "kb_context_found": bool(matches),
            "retrieval_score":  round(retrieval_score, 3),
            "matches":          matches,
        }

    except Exception as e:
        logging.error(f"Error retrieving context: {e}")
        return {
            "context_text":     "",
            "kb_context_found": False,
            "retrieval_score":  0.0,
            "matches":          [],
            "error":            str(e),
        }


if __name__ == "__main__":
    ingest_documents()