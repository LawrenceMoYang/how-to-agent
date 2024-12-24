import os
import pickle
import numpy as np
import faiss
import sys

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from src.config import EMBEDDER_MODELS
from src.embedder import Embedder
from src.index_utils import build_index


class DocIndex:
    def __init__(self, index_path=None, embedder = None, vector_prime_tokenizer_path=None):
        self.index = None
        self.urls = None
        self.embedder = embedder
        self.chunks = None
        self.vector_prime_tokenizer_path = vector_prime_tokenizer_path

        # Load index.
        if not index_path or not os.path.exists(index_path):
            print(f"No index at {index_path}")
            return

        print(f"Loading index from {index_path}")
        self.load_data(index_path, embedder)

    def build(self, content_paths: list, index_path: str, embedder_model_name: str, chunk_size:int, dev: bool= False):
        # Don't override.
        if os.path.exists(index_path):
            print(f"Index exists at {index_path}")
            return

        embedder = Embedder(embedder_model_name=embedder_model_name,
                            vector_prime_tokenizer_path=self.vector_prime_tokenizer_path)
        build_index(content_paths, index_path, embedder, chunk_size, dev)
        # Build the index.
        self.load_data(index_path)

    def retrieve_question_embedding(self, question):
        # Generate embedding for the query
        query_embedding = self.embedder.generate_embedding(question)
        query_embedding = query_embedding.astype(np.float32).reshape(1, -1)
        faiss.normalize_L2(query_embedding)

        return query_embedding
    
    def search_with_question_emb(self, query_embedding, top_k=5):
        # Perform search in the FAISS index
        _, indices = self.index.search(query_embedding, top_k)

        # Retrieve the corresponding documents
        res_chunks = [self.chunks[i] for i in indices[0]]
        res_urls = [self.urls[i] for i in indices[0]]

        return res_chunks, res_urls


    def search(self, question, top_k=5):
        """Searches for the top-k most similar documents to the query."""
        query_embedding = self.retrieve_question_embedding(question)

        return self.search_with_question_emb(query_embedding, top_k)
        

    def search_full(self, question, top_k=5) -> list[dict]:
        """Search for the top-k most similar documents to the query with metadata"""
        res_chunks, res_urls = self.search(question, top_k)

        results = [
            {'chunk': chunk, 'url': url, 'actions': None, 'tips': None}
            for chunk, url in zip(res_chunks, res_urls)
        ]
        return results

    def load_data(self, index_path: str, embedder_model_name_or_path=None):
        # Load FAISS index and metadata
        with open(index_path, 'rb') as f:
            data = pickle.load(f)
            self.index = data["index"]
            self.urls = data["urls"]
            embedder_model_name = embedder_model_name_or_path or data["embedder_model"]
            self.embedder = Embedder(embedder_model_name=embedder_model_name,
                                     vector_prime_tokenizer_path=self.vector_prime_tokenizer_path)
            if self.embedder.embedder_model_name != data["embedder_model"]:
                print(f"Warning: Embedder model name mismatch. Expected {data['embedder_model']}, "
                      f"but got {self.embedder.embedder_model_name}")

            self.chunks = data["chunks"]


if __name__ == "__main__":

    embedder_models = ['MPNet-V2', 'Vector-Prime']
    contents = ["../demos/demo_v0/resources/content/sellercenter_crawled_data.json",
                "../demos/demo_v0/resources/content/help_guides_data.json"]

    for embedder_model in embedder_models:
        d = DocIndex(index_path = f"../{EMBEDDER_MODELS[embedder_model]['index_path']}")
        d.build(content_paths = contents,
                index_path = f"../{EMBEDDER_MODELS[embedder_model]['index_path']}",
                embedder_model_name=EMBEDDER_MODELS[embedder_model]["model_name"],
                chunk_size=EMBEDDER_MODELS[embedder_model]["chunk_size"])
        print(d.search(question="how to sell", top_k=3))