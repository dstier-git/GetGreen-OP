from pathlib import Path
import threading

import numpy as np
import pandas as pd
# FAISS check and fallback implemented by Codex


try:
    import faiss  # type: ignore
    _HAS_FAISS = True
except ImportError:
    faiss = None
    _HAS_FAISS = False

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


EMBED_DIM = 384
MODEL_NAME = "all-MiniLM-L6-v2"
BASE_DIR = Path(__file__).resolve().parent
CORE_DATA_DIR = BASE_DIR.parent / "core_data"
DATA_PATH = CORE_DATA_DIR / "articles_cleaned_filtered.csv"
INDEX_PATH = BASE_DIR / "faiss_index.bin"
EMBEDDINGS_PATH = BASE_DIR / "article_embeddings.npy"

_documents = None
_index = None
_embeddings = None
_embed_model = None
_lock = threading.Lock()


def build_index_once() -> None:
    """
    Build the FAISS index over the articles corpus *once*.

    - Reads `articles_cleaned_filtered.csv`
    - Computes embeddings for all documents
    - Writes `faiss_index.bin` when FAISS is installed
    - Writes `article_embeddings.npy` when FAISS is unavailable
    - Prints progress so you know when it's done
    """
    global _documents, _index, _embeddings

    print(f"[vector_retriever] Starting one-time embedding + index build...")
    print(f"[vector_retriever] Corpus CSV: {DATA_PATH}")
    print(
        f"[vector_retriever] Retrieval backend: {'faiss' if _HAS_FAISS else 'numpy (faiss not installed)'}"
    )

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"[vector_retriever] Missing corpus CSV at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    _documents = (
        df["Title"].fillna("") + "\n\n" + df["scraped_text"].fillna("")
    ).tolist()
    print(f"[vector_retriever] Loaded {len(_documents)} documents.")

    if SentenceTransformer is None:
        raise ModuleNotFoundError(
            "[vector_retriever] sentence_transformers is required to build embeddings. "
            "Install with `pip install sentence-transformers`."
        )

    model = SentenceTransformer(MODEL_NAME)
    print(f"[vector_retriever] Loaded embedding model '{MODEL_NAME}'.")

    embeddings = np.asarray(model.encode(_documents, show_progress_bar=True), dtype="float32")
    print(f"[vector_retriever] Computed embeddings with shape {embeddings.shape}.")

    if _HAS_FAISS:
        index = faiss.IndexFlatL2(EMBED_DIM)
        index.add(embeddings)
        faiss.write_index(index, str(INDEX_PATH))
        _index = index
        _embeddings = None
        print(
            f"[vector_retriever] Index build complete. "
            f"Stored {index.ntotal} vectors to {INDEX_PATH}"
        )
        return

    np.save(EMBEDDINGS_PATH, embeddings)
    _embeddings = embeddings
    _index = None
    print(
        f"[vector_retriever] Built NumPy embedding store with {len(_documents)} vectors at "
        f"{EMBEDDINGS_PATH}"
    )


def _load_documents_and_index():
    """Load documents and retrieval index/store."""
    global _documents, _index, _embeddings

    if _documents is not None and (_index is not None or _embeddings is not None):
        return

    with _lock:
        if _documents is not None and (_index is not None or _embeddings is not None):
            return

        if not DATA_PATH.exists():
            raise FileNotFoundError(f"[vector_retriever] Missing corpus CSV at {DATA_PATH}")

        df = pd.read_csv(DATA_PATH)
        _documents = (
            df["Title"].fillna("") + "\n\n" + df["scraped_text"].fillna("")
        ).tolist()

        if _HAS_FAISS:
            if not INDEX_PATH.exists():
                print(
                    f"[vector_retriever] Missing FAISS index at {INDEX_PATH}. "
                    f"Building it now..."
                )
                if SentenceTransformer is None:
                    print(
                        "[vector_retriever] Cannot build FAISS index because "
                        "`sentence_transformers` is not installed."
                    )
                    return
                build_index_once()
                return
            _index = faiss.read_index(str(INDEX_PATH))
            return

        if EMBEDDINGS_PATH.exists():
            _embeddings = np.load(EMBEDDINGS_PATH)
            if len(_embeddings) == len(_documents):
                return
            print(
                f"[vector_retriever] Embedding count mismatch for {EMBEDDINGS_PATH}. "
                f"Rebuilding embeddings..."
            )

        print(
            f"[vector_retriever] Missing embedding store at {EMBEDDINGS_PATH}. "
            f"Building it now..."
        )
        if SentenceTransformer is None:
            print(
                "[vector_retriever] Cannot build embedding store because "
                "`sentence_transformers` is not installed."
            )
            return
        build_index_once()


def _load_model():
    """Lazily load the sentence-transformer model for query encoding."""
    global _embed_model
    if _embed_model is not None:
        return

    with _lock:
        if _embed_model is not None:
            return
        if SentenceTransformer is None:
            print(
                "[vector_retriever] sentence_transformers is not installed. "
                "Skipping retrieval."
            )
            return
        _embed_model = SentenceTransformer(MODEL_NAME)


def _top_k_by_cosine(query_embedding: np.ndarray, embeddings: np.ndarray, k: int):
    if embeddings.size == 0:
        return np.array([], dtype=int)

    query_vec = np.asarray(query_embedding, dtype="float32").ravel()
    doc_vecs = np.asarray(embeddings, dtype="float32")

    query_norm = np.linalg.norm(query_vec)
    doc_norms = np.linalg.norm(doc_vecs, axis=1)
    denom = np.maximum(doc_norms * max(query_norm, 1e-12), 1e-12)
    scores = np.dot(doc_vecs, query_vec) / denom

    top_k = max(1, min(k, len(scores)))
    top_idx = np.argsort(-scores)[:top_k]
    return top_idx


def retrieve_relevant_docs(query: str, k: int = 2) -> str:
    """
    Return the top-k documents stitched into a single context block.

    Document embeddings are **not** recomputed here — they should be built once
    by running this module as a script:

        python core/backend/vector_retriever.py
    """
    if not query:
        print("[vector_retriever] Empty query string received; skipping retrieval.")
        return ""

    print("[vector_retriever] Loading documents and retrieval index/store (if not already loaded)...")
    _load_documents_and_index()
    if _documents is None:
        print("[vector_retriever] ERROR: Documents not loaded.")
        return ""

    print(f"[vector_retriever] Documents loaded: {len(_documents)}")
    if _HAS_FAISS and _index is not None:
        print(f"[vector_retriever] Index size (ntotal): {_index.ntotal}")
    elif _embeddings is not None:
        print(f"[vector_retriever] Embedding store size: {len(_embeddings)}")
    else:
        print("[vector_retriever] ERROR: No retrieval backend is loaded.")
        return ""

    print("[vector_retriever] Loading embedding model (if not already loaded)...")
    _load_model()
    if _embed_model is None:
        print("[vector_retriever] ERROR: Embedding model not loaded.")
        return ""

    print("[vector_retriever] Encoding query to embedding...")
    q_emb = np.asarray(_embed_model.encode([query]), dtype="float32")
    print(f"[vector_retriever] Query embedding shape: {getattr(q_emb, 'shape', 'unknown')}")

    if _HAS_FAISS and _index is not None:
        print(f"[vector_retriever] Searching top-{k} nearest documents in FAISS index...")
        _, hit_indices = _index.search(q_emb, k)
        indices = hit_indices[0]
    else:
        print(f"[vector_retriever] Searching top-{k} nearest documents with NumPy cosine similarity...")
        indices = _top_k_by_cosine(q_emb[0], _embeddings, k)

    selected = []
    for idx in indices:
        if 0 <= idx < len(_documents):
            selected.append(_documents[idx])

    print(f"[vector_retriever] Retrieved {len(selected)} article(s) from index.")
    return "\n\n".join(selected)


if __name__ == "__main__":
    # One-off embedding + index build entrypoint.
    # Run this from the project root:
    #   python core/backend/vector_retriever.py
    build_index_once()
