"""llama-cpp-python embedding with auto-download (GGUF via huggingface_hub)."""
import os
from pathlib import Path
from typing import List, Union, Optional

import numpy as np

# Model config
MODEL_FILENAME = "nomic-embed-text-v1.5.Q4_K_M.gguf"
MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "models"
MODEL_PATH = MODEL_DIR / MODEL_FILENAME
EMBEDDING_DIM = 768

_model_instance = None


def _download_model() -> Path:
    """Auto-download GGUF model if missing."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if MODEL_PATH.exists():
        return MODEL_PATH

    try:
        from huggingface_hub import hf_hub_download
        path = hf_hub_download(
            repo_id="nomic-ai/nomic-embed-text-v1.5-GGUF",
            filename=MODEL_FILENAME,
            cache_dir=str(MODEL_DIR),
            local_dir=str(MODEL_DIR),
        )
        return Path(path)
    except Exception as e:
        print(f"[embedder] ERROR: Failed to download model: {e}")
        raise


def get_embedder() -> object:
    """Singleton llama-cpp Llama instance for embeddings."""
    global _model_instance
    if _model_instance is None:
        import llama_cpp
        model_path = _download_model()
        n_ctx = int(os.environ.get("LLAMA_CTX_SIZE", "2048"))
        n_threads = int(os.environ.get("LLAMA_N_THREADS", "4"))
        _model_instance = llama_cpp.Llama(
            model_path=str(model_path),
            n_ctx=n_ctx,
            n_threads=n_threads,
            embedding=True,
            verbose=False,
        )
    return _model_instance


def embed_texts(texts: Union[str, List[str]]) -> List[List[float]]:
    """Generate embeddings for one or more texts. Returns list of [768] vectors."""
    if isinstance(texts, str):
        texts = [texts]

    embedder = get_embedder()
    results = []
    for text in texts:
        emb = embedder.create_embedding(text)
        vec = emb["data"][0]["embedding"]
        # Normalize to unit vector (cosine similarity)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = [float(v / norm) for v in vec]
        results.append(vec)

    return results


def embed_single(text: str) -> List[float]:
    """Embed a single text string. Returns normalized 768-dim vector."""
    return embed_texts(text)[0]
