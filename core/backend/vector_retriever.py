from pathlib import Path
import threading

import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer


EMBED_DIM = 384
MODEL_NAME = "all-MiniLM-L6-v2"
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR.parent.parent / "data" / "articles.csv"
INDEX_PATH = BASE_DIR / "faiss_index.bin"

_documents = None
_index = None
_embed_model = None
_lock = threading.Lock()


def build_index_once() -> None:
    """
    Build the FAISS index over the articles corpus *once*.

    - Reads `articles.csv`
    - Computes embeddings for all documents
    - Writes `faiss_index.bin`
    - Prints progress so you know when it's done
    """
    global _documents

    print(f"[vector_retriever] Starting one-time embedding + index build...")
    print(f"[vector_retriever] Corpus CSV: {DATA_PATH}")
    print(f"[vector_retriever] Target index: {INDEX_PATH}")

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"[vector_retriever] Missing corpus CSV at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    _documents = (
        df["Title"].fillna("") + "\n\n" + df["scraped_text"].fillna("")
    ).tolist()
    print(f"[vector_retriever] Loaded {len(_documents)} documents.")

    model = SentenceTransformer(MODEL_NAME)
    print(f"[vector_retriever] Loaded embedding model '{MODEL_NAME}'.")

    embeddings = model.encode(_documents, show_progress_bar=True)
    print(f"[vector_retriever] Computed embeddings with shape {embeddings.shape}.")

    index = faiss.IndexFlatL2(EMBED_DIM)
    index.add(embeddings)
    faiss.write_index(index, str(INDEX_PATH))

    print(
        f"[vector_retriever] Index build complete. "
        f"Stored {index.ntotal} vectors to {INDEX_PATH}"
    )


def _load_documents_and_index():
    """Load documents and FAISS index (no document embedding is done here)."""
    global _documents, _index

    if _index is not None and _documents is not None:
        return

    with _lock:
        if _index is not None and _documents is not None:
            return

        if not DATA_PATH.exists():
            raise FileNotFoundError(f"[vector_retriever] Missing corpus CSV at {DATA_PATH}")

        df = pd.read_csv(DATA_PATH)
        _documents = (
            df["Title"].fillna("") + "\n\n" + df["scraped_text"].fillna("")
        ).tolist()

        if not INDEX_PATH.exists():
            raise FileNotFoundError(
                f"[vector_retriever] Missing FAISS index at {INDEX_PATH}. "
                f"Run `python {__file__}` once to build it."
            )

        _index = faiss.read_index(str(INDEX_PATH))


def _load_model():
    """Lazily load the sentence-transformer model for query encoding."""
    global _embed_model
    if _embed_model is not None:
        return

    with _lock:
        if _embed_model is not None:
            return
        _embed_model = SentenceTransformer(MODEL_NAME)


def retrieve_relevant_docs(query: str, k: int = 2) -> str:
    """
    Return the top-k documents stitched into a single context block.

    Document embeddings are **not** recomputed here — they should be built once
    by running this module as a script:

        python backend/Response/vector_retriever.py
    """
    if not query:
        print("[vector_retriever] Empty query string received; skipping retrieval.")
        return ""

    print("[vector_retriever] Loading documents and FAISS index (if not already loaded)...")
    _load_documents_and_index()
    if _index is None or _documents is None:
        print("[vector_retriever] ERROR: Index or documents not loaded.")
        return ""
    print(f"[vector_retriever] Documents loaded: {len(_documents)}")
    print(f"[vector_retriever] Index size (ntotal): {_index.ntotal}")

    print("[vector_retriever] Loading embedding model (if not already loaded)...")
    _load_model()
    if _embed_model is None:
        print("[vector_retriever] ERROR: Embedding model not loaded.")
        return ""

    print("[vector_retriever] Encoding query to embedding...")
    q_emb = _embed_model.encode([query])
    print(f"[vector_retriever] Query embedding shape: {getattr(q_emb, 'shape', 'unknown')}")

    print(f"[vector_retriever] Searching top-{k} nearest documents in FAISS index...")
    _, hit_indices = _index.search(q_emb, k)

    selected = []
    for idx in hit_indices[0]:
        if 0 <= idx < len(_documents):
            selected.append(_documents[idx])

    print(f"[vector_retriever] Retrieved {len(selected)} article(s) from index.")
    return "\n\n".join(selected)


if __name__ == "__main__":
    # One-off embedding + index build entrypoint.
    # Run this from the project root:
    #   python backend/Response/vector_retriever.py
    build_index_once()
