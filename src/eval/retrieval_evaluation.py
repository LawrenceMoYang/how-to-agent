import os
import pickle
from tqdm import tqdm
import sys
import argparse
import json
from collections import defaultdict

# Add the parent directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.docindex import DocIndex


MODELS = {
    'MPNet-V2': 'sentence-transformers/all-mpnet-base-v2',
    'Vector-Prime': 'EBAY_INTERNAL_VECTOR_PRIME',
}


def calculate_mAP(hit_counts, total_cnt):
    """
    Calculate the Mean Average Precision (mAP) based on hit counts and the total count.
    
    Parameters:
    hit_counts (dict): A dictionary where the key is the rank (1-based index), for example: {1: 1820, 2: 2132, 3: 2317, 4: 2440, 5: 2531}) 
                       and the value is the number of hits up to that rank.
    total_cnt (int): The total number of items for normalization.
    
    Returns:
    float: The calculated mAP value.
    """

    # Determine the maximum rank (k) for which we have hit counts
    k = max(hit_counts.values())

    # Initialize a list to store hits at each rank (0 to k)
    hit_in_k = [0] * (k + 1)

    # Populate the list with cumulative hits at each rank from hit_counts
    for idx, count in hit_counts.items():
        hit_in_k[idx] = count

    # Calculate hits at each individual rank by subtracting cumulative values
    for i in range(k, 0, -1):
        hit_in_k[i] = hit_in_k[i] - hit_in_k[i - 1]

    # Compute the mAP by summing the precision at each rank and normalizing by total count
    map = sum([hit_in_k[i] * 1 / i for i in range(1, k + 1)]) / total_cnt

    return map

class DocumentRetrievalEvaluator:
    def __init__(self, document_path, chunk_index_path, chunk_size=384, model_name='MPNet-V2', question_emb_cach_path=None):
        """
        Initialize the evaluator.
        
        :param base_path: Base directory for index and content files.
        :param embedder_model: Dictionary containing embedder model details (name, index_path).
        :param top_ks: List of top-k values for evaluation.
        """
        self.model_name = model_name
        self.model_name = MODELS[model_name]
        
        self._build_index(document_path, chunk_index_path, chunk_size, MODELS[model_name])

        if question_emb_cach_path and os.path.exists(question_emb_cach_path):
            print("load cached question ebedding from ", question_emb_cach_path)
            with open(question_emb_cach_path, "rb") as f:
                self.question_embedding_cache  = pickle.load(f)
        else:
            self.question_embedding_cache = {}

    def _build_index(self, content_path, chunk_index_path, chunk_size, embedder_model_name):
        """
        Build the document index.
        
        :param content_path: Path to the JSON content file for building the index.
        """
        self.d = DocIndex(index_path=chunk_index_path)
        self.d.build(
            content_paths=[content_path],
            index_path=chunk_index_path,
            embedder_model_name=embedder_model_name,
            chunk_size=chunk_size
        )

    def search(self, question, top_k):
        """
        Search the index for a given question.
        
        :param question: The question string.
        :param top_k: The number of top results to retrieve.
        :return: Tuple of (question, retrieved URLs).
        """
        if question not in self.question_embedding_cache:
            query_embedding = self.d.retrieve_question_embedding(question)

            self.question_embedding_cache[question] = query_embedding
        else:
            query_embedding = self.question_embedding_cache[question]

        _, res_urls =  self.d.search_with_question_emb(query_embedding, top_k)

        return res_urls

    def evaluate(self, questions, top_k):
        """
        Evaluate the retrieval performance for given questions.
        
        :param questions: List of dictionaries containing 'url' and 'question'.
        :return: Dictionary of hit counts for each top_k value.
        """
        hit_counts = defaultdict(int)
        for question in tqdm(questions, desc="Evaluating Questions"):
            gt_url = question["url"]
            q = question["question"]
            recall_urls = self.search(question=q, top_k=top_k)
            
            hit = 0
            for idx, url in enumerate(recall_urls):
                if url == gt_url:
                    hit = 1

                hit_counts[idx+1] += hit

        mAP = calculate_mAP(hit_counts, len(questions))
        hit_rate = {k: hit / len(questions) for k, hit in hit_counts.items() }

        return hit_rate, mAP

    def display_results(self, hit_cnt, total_questions):
        """
        Display the evaluation results.
        
        :param hit_cnt: Dictionary of hit counts.
        :param total_questions: Total number of questions evaluated.
        """
        for k, hits in hit_cnt.items():
            percentage = hits / total_questions * 100
            print(f"Hit@{k}: {hits}/{total_questions} ({percentage:.2f}%)")


def main(questions_path, document_path, chunk_index_path, top_k=5, chunk_size=384, index_model_name='MPNet-V2', question_emb_cach_path=None, question_type="standard"):
    assert os.path.exists(questions_path), f"The questions file does not exist: {questions_path}"
    assert os.path.exists(document_path), f"The document file does not exist: {document_path}"

    with open(questions_path, 'r') as file:
        questions = json.load(file)


    evaluator = DocumentRetrievalEvaluator(
        document_path=document_path,
        chunk_index_path=chunk_index_path,
        model_name=index_model_name,
        chunk_size=chunk_size,
        question_emb_cach_path=question_emb_cach_path,
    )

    if question_type == "standard":
        eval_questions  = [{
            "question": q["question"],
            "url": q["url"]
        }
        for q in questions]
    elif  question_type == "variant":
        eval_questions = []
        for q in questions:
            variant_qs = [{
                "question": va,
                "url": q["url"]
            }
            for va in q["variants"]]

            eval_questions += variant_qs

    else:
        raise ValueError("question document type should be standard or variant")
    
    assert len(eval_questions), "please provide the qeustion to evaluate"
    
    hit_rate, mAP = evaluator.evaluate(questions=eval_questions, top_k=top_k)
   
    return hit_rate, mAP

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate document retrieval system.")

    parser.add_argument("--index_model_name", default="MPNet-V2", type=str, help="Model name for embedding.")
    parser.add_argument("--topk", default=5, type=int, help="Number of top results to evaluate.")
    parser.add_argument("--questions_path", type=str, required=True, help="Path to the questions JSON file.")
    parser.add_argument("--document_path", type=str, required=True, help="Path to the document JSON file.")
    parser.add_argument("--chunk_index_path", type=str, required=True, help="Path to the chunk index directory.")
    parser.add_argument("--question_emb_cach_path", type=str, help="Path to cache question embeddings.")

    args = parser.parse_args()

    main(
        questions_path=args.questions_path,
        document_path=args.document_path,
        chunk_index_path=args.chunk_index_path,
        top_k=args.topk,
        index_model_name=args.index_model_name,
        question_emb_cach_path=args.question_emb_cach_path,
    )
