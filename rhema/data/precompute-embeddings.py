#!/usr/bin/env python3
"""
Pre-compute verse embeddings using sentence-transformers + MPS GPU.

Outputs match the Rust binary format expected by HnswVectorIndex::load():
  - embeddings file: flat f32 array, little-endian, dim floats per verse
  - ids file: flat i64 array, little-endian, one per verse

Usage:
  python3 data/precompute-embeddings.py

Requires (already in /tmp/optimum-venv):
  pip install sentence-transformers torch
"""

import json
import struct
import time
from pathlib import Path

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

# ── Paths ───────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
VERSES_PATH = ROOT / "data" / "verses-for-embedding.json"
EMB_OUT = ROOT / "embeddings" / "kjv-qwen3-0.6b.bin"
IDS_OUT = ROOT / "embeddings" / "kjv-qwen3-0.6b-ids.bin"
MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"

# ── Device ──────────────────────────────────────────────────────────
if torch.backends.mps.is_available():
    DEVICE = "mps"
elif torch.cuda.is_available():
    DEVICE = "cuda"
else:
    DEVICE = "cpu"


def main():
    print(f"\n=== Rhema Verse Embedding Pre-computation (Python) ===")
    print(f"Device: {DEVICE}")
    print(f"Model:  {MODEL_NAME}")

    # Load verses
    print(f"\nLoading verses from {VERSES_PATH}...")
    with open(VERSES_PATH) as f:
        entries = json.load(f)
    print(f"  {len(entries)} verses loaded")

    ids = [e["id"] for e in entries]
    # No manual prefix — sentence-transformers' Qwen3 document prompt is ""
    texts = [e["text"] for e in entries]

    # Load model
    print(f"\nLoading model (this may download on first run)...")
    model = SentenceTransformer(MODEL_NAME, device=DEVICE)
    dim = model.get_sentence_embedding_dimension()
    print(f"  Embedding dimension: {dim}")
    print(f"  Prompts: {model.prompts}")

    # Encode in batches
    print(f"\nEncoding {len(texts)} verses...")
    t0 = time.time()
    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,  # L2 normalize (matches Rust code)
    )
    elapsed = time.time() - t0
    print(f"  Done in {elapsed:.1f}s ({len(texts) / elapsed:.0f} verses/sec)")

    # Write embeddings binary (flat f32, little-endian)
    EMB_OUT.parent.mkdir(parents=True, exist_ok=True)
    print(f"\nWriting embeddings to {EMB_OUT}...")
    emb_array = np.asarray(embeddings, dtype="<f4")  # little-endian float32
    emb_array.tofile(str(EMB_OUT))
    emb_size = EMB_OUT.stat().st_size
    print(f"  {emb_size:,} bytes ({emb_size / 1024 / 1024:.1f} MB)")

    # Write IDs binary (flat i64, little-endian)
    print(f"Writing IDs to {IDS_OUT}...")
    ids_array = np.array(ids, dtype="<i8")  # little-endian int64
    ids_array.tofile(str(IDS_OUT))
    ids_size = IDS_OUT.stat().st_size
    print(f"  {ids_size:,} bytes")

    # Verify
    expected_emb = len(entries) * dim * 4
    expected_ids = len(entries) * 8
    assert emb_size == expected_emb, f"Embedding size mismatch: {emb_size} != {expected_emb}"
    assert ids_size == expected_ids, f"IDs size mismatch: {ids_size} != {expected_ids}"

    print(f"\n=== Done! {len(entries)} verses x {dim} dims ===\n")


if __name__ == "__main__":
    main()
