import os
import argparse
from tqdm import tqdm
import json
from src.eval.llm_question_generator import generate_questions


# Define the synthetic question prompt as a constant
propmt_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "./prompts/synthetic_question_generator.txt"))
with open(propmt_file_path, 'r') as p_file:
    SYNTHETIC_QUESTION_PROMPT = p_file.read()


def generate_synthetic_questions(documents, output_file):
    """
    Generate synthetic questions from a list of documents and save them to a JSON file.

    Args:
        documents (list): List of dictionaries, where each dictionary contains "url" and "content" keys.
        output_file (str): Path to the output JSON file to store generated questions.

    Returns:
        tuple: A list of generated questions and a set of visited URLs.
    """

    questions = []
    visited_urls = set()
    if os.path.exists(output_file):
        print(output_file)
        with open(output_file, 'r') as json_file:
            questions = json.load(json_file)
            visited_urls = set([q['url'] for q in questions])
            print(f"proload question for #{len(visited_urls)} documents")
        
   # Calculate the remaining documents to process
    rest_doc_cnt = len(documents) - len(visited_urls)

    if rest_doc_cnt == 0:
        print("All documents have generated questions. Skipping.")
        return questions, visited_urls
    
    print(f"Starting to generate questions for {rest_doc_cnt} documents...")

    count = 0

    # Use tqdm to show progress
    for doc in tqdm(documents, desc="Generating Questions"):
        url = doc["url"]

        # Skip documents that have already been processed
        if url not in visited_urls:
            try:
                # Generate questions using the provided function
                qs = generate_questions(str(SYNTHETIC_QUESTION_PROMPT), doc["content"])

                if qs:
                    # Append new questions to the list
                    questions += [{
                        "question": q["question"], 
                        "answer": q["answer"],
                        "url": url
                    } for q in qs]
                    visited_urls.add(url)
                    count += 1

                    # Save to file every time the count reaches a multiple of 50
                    if count % 20 == 0:
                        with open(output_file, 'w') as json_file:
                            json.dump(questions, json_file, indent=4)
                        print(f"Intermediate save: wrote #{len(visited_urls)} documents' qeustions so far")

            except Exception as e:
                # Log any exceptions during question generation
                print(f"Error processing URL {url}: {e}")

    # Save all generated questions to the output file
    with open(output_file, 'w') as json_file:
        json.dump(questions, json_file, indent=4)

    print(f"Finished generating questions. Total: {len(questions)}")
    return questions, visited_urls

def main(input_data_path, output_data_path):
    """
    Main function to generate synthetic questions from documents.

    Args:
        input_data_path (str): Path to the input JSON file containing documents.
        output_data_path (str): Path to the output JSON file for saving questions.
    """
    if not os.path.exists(input_data_path):
        raise ValueError(f"The input path does not exist: {input_data_path}")
    
    # Load documents from the input JSON file
    with open(input_data_path, 'r') as file:
        documents = json.load(file)
    
    questions, _ = generate_synthetic_questions(documents, output_data_path)

    return questions


if __name__ == "__main__":
    # python src/eval/synthetic_question_generator.py --input_data_path demos/demo_v0/resources/crawl_data/sellercenter_crawled_data.json  --output_data_path data/sellercenter_question.json

    parser = argparse.ArgumentParser(description="Generate synthetic questions from documents.")

    # Command-line arguments
    parser.add_argument(
        "--input_data_path",
        help="The input document path (JSON file).",
        type=str,
        required=True
    )
    parser.add_argument(
        "--output_data_path",
        help="The output document path (JSON file).",
        type=str,
        required=True
    )

    args = parser.parse_args()

    # Run the main function
    main(args.input_data_path, args.output_data_path)