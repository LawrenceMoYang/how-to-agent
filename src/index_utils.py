import os
import pickle
import faiss
import numpy as np
from transformers import AutoTokenizer
import json
from tqdm import tqdm

from src.embedder import Embedder


def build_faiss_index(embeddings: np.array) -> faiss.IndexFlatIP:
    """Builds a FAISS index for the provided embeddings."""
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    return index


def split_into_chunks(text: str, tokenizer: AutoTokenizer, chunk_size=384, overlap=50):
    tokens = tokenizer.encode(text, add_special_tokens=False)
    chunks = []
    for i in range(0, len(tokens), chunk_size - overlap):
        chunk_tokens = tokens[i:i + chunk_size]
        chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
        chunks.append(chunk_text)

    return chunks


def build_index(sources_files: list, index_file_path: str, embedder: Embedder, chunk_size: int, dev: bool = False):
    all_data = []
    for sources_file in sources_files:
        print(f'Loading content from {os.getcwd() + "/" + sources_file}')
        with open(sources_file, 'r', encoding='utf-8') as json_file:
            json_data = json.load(json_file)
            all_data.extend(json_data)

    if dev:
        all_data = all_data[:10]
        index_file_path = index_file_path.replace(".pkl", "_dev.pkl")
    print(f"Building index for {len(all_data)} documents")

    embeddings, urls, chunks = [], [], []
    for document in tqdm(all_data, desc="Processing documents"):
        content = document.get("content", "")
        url = document.get("url", "")

        # Split the text into chunks
        text_chunks = split_into_chunks(content, embedder.tokenizer, chunk_size)

        # Index the chunks.
        for chunk in text_chunks:
            urls.append(url)
            embeddings.append(embedder.generate_embedding(chunk))
            chunks.append(chunk)

    print(f"Generated embeddings for {len(embeddings)} chunks")

    # Stack embeddings into a single numpy array
    embeddings = np.vstack(embeddings).astype(np.float32)
    faiss.normalize_L2(embeddings)

    # Build FAISS index
    index = build_faiss_index(embeddings)

    # Save FAISS index and metadata together in a pickle file
    print(f"Index build completed, saving to {index_file_path}")
    with open(index_file_path, 'wb') as f:
        pickle.dump({"index": index,
                     "urls": urls,
                     "chunks": chunks,
                     "embedder_model": embedder.embedder_model_name}, f)