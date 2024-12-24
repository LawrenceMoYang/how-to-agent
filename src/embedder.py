import os
import site
import sys
import time

site_packages_path = site.getsitepackages()[0]
sys.path.insert(0, site_packages_path) # import datasets pkg from python packages instead of krylov propeller

import numpy as np
from sentence_transformers import SentenceTransformer
from pychomsky.chembed import EbayLLMEmbeddingWrapper
from transformers import AutoTokenizer

class Embedder:
    def __init__(self, embedder_model_name, vector_prime_tokenizer_path: str=None):
        self.cache_folder = None
        if '/Users' not in os.path.expanduser("~"):
            self.cache_folder = "/shared-data"  # shared data path in the docker container

        vector_prime_tokenizer_path = vector_prime_tokenizer_path if vector_prime_tokenizer_path else\
            os.path.join(os.path.dirname(__file__), "vector_prime_tokenizer")

        self.embedder_model_name = embedder_model_name

        if self.embedder_model_name == "EBAY_INTERNAL_VECTOR_PRIME":
            self.embedder = EbayLLMEmbeddingWrapper(model_name="EBAY_INTERNAL_VECTOR_PRIME")
            if vector_prime_tokenizer_path:
                self.tokenizer = AutoTokenizer.from_pretrained(vector_prime_tokenizer_path, cache_folder=self.cache_folder)
            self.tokenizer = AutoTokenizer.from_pretrained(vector_prime_tokenizer_path, cache_folder=self.cache_folder)

        else:
            self.embedder = SentenceTransformer(self.embedder_model_name, cache_folder=self.cache_folder)
            self.tokenizer = AutoTokenizer.from_pretrained(self.embedder_model_name, cache_dir=self.cache_folder)


    def generate_embedding(self, text: str, max_retries: int = 3, retry_delay: float = 1.0) -> np.array:
        attempts = 0
        while attempts < max_retries:
            try:
                if self.embedder_model_name == "EBAY_INTERNAL_VECTOR_PRIME":
                    return np.array(self.embedder.embed_query(text=text))
                return self.embedder.encode(text, convert_to_tensor=False)
            except Exception as e:
                print(f"Error generating embedding (attempt {attempts + 1}/{max_retries}): {e}")
                attempts += 1
                time.sleep(retry_delay)
        raise RuntimeError("Failed to generate embedding after multiple attempts")