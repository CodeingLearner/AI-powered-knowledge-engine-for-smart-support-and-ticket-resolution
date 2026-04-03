import os
import sys
import logging
import shutil
from tqdm import tqdm

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'app'))

import rag_engine
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

logging.basicConfig(level=logging.INFO, format='%(message)s')
logging.getLogger("httpx").setLevel(logging.WARNING)


def manual_ingest():
    print(f"\n📂 Checking: {rag_engine.DATA_RAW_DIR}")

    os.makedirs(rag_engine.DATA_RAW_DIR,       exist_ok=True)
    os.makedirs(rag_engine.DATA_PROCESSED_DIR, exist_ok=True)

    files = [
        f for f in os.listdir(rag_engine.DATA_RAW_DIR)
        if os.path.isfile(os.path.join(rag_engine.DATA_RAW_DIR, f))
    ]

    if not files:
        print("No new documents found.")
        return

    print(f"Found {len(files)} file(s). Loading...")

    documents = []
    for f in tqdm(files, desc="Loading Files"):
        loaded = rag_engine._load_file(os.path.join(rag_engine.DATA_RAW_DIR, f), f)
        documents.extend(loaded)

    if not documents:
        print("No valid content extracted.")
        return

    print(f"\nSplitting {len(documents)} page(s) into chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    docs = splitter.split_documents(documents)
    print(f"Total chunks: {len(docs)}")

    print(f"\nGenerating embeddings with '{rag_engine.EMBEDDING_MODEL}'...")
    # ✅ No model arg needed — defaults to EMBEDDING_MODEL constant
    embeddings = rag_engine.OllamaEmbeddings()

    db = None
    if os.path.exists(rag_engine.FAISS_INDEX_PATH):
        try:
            db = FAISS.load_local(
                rag_engine.FAISS_INDEX_PATH, embeddings,
                allow_dangerous_deserialization=True
            )
            print("Loaded existing index.")
        except:
            db = None

    batch_size = 5
    for i in tqdm(range(0, len(docs), batch_size), desc="Embedding Chunks"):
        batch = docs[i: i + batch_size]
        if db is None:
            db = FAISS.from_documents(batch, embeddings)
        else:
            db.add_documents(batch)

    print("\nSaving index...")
    db.save_local(rag_engine.FAISS_INDEX_PATH)

    print("Cleaning up raw files...")
    for f in files:
        try:
            shutil.move(
                os.path.join(rag_engine.DATA_RAW_DIR, f),
                os.path.join(rag_engine.DATA_PROCESSED_DIR, f)
            )
        except Exception as e:
            print(f"  Could not move '{f}': {e}")

    print("\n✅ Ingestion complete! Run your main app now.")


if __name__ == "__main__":
    manual_ingest()