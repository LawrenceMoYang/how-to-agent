
import json
from pychomsky.chchat import EbayLLMChatWrapper
import argparse
from src.eval.llm_question_generator import generate_questions


import os
import json

# Define the synthetic question prompt as a constant
propmt_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "./prompts/question_variation_generator.txt"))
with open(propmt_file_path, 'r') as p_file:
    QUESTION_VARIANT_PROMPT = p_file.read()

def generate_question_variants(questions, output_file):
    print(f"Start quetion variants generation fro #{len(questions)} questions")

    question_variants = []
    visited_questions = set()
    
    # If the file exists, load the existing questions
    if os.path.exists(output_file):
        with open(output_file, 'r') as json_file:
            question_variants = json.load(json_file)
            visited_questions = set([q['original_question'] for q in question_variants])
            print(f"Loaded #{len(visited_questions)} visited_questions")
    
    count = 0  # Counter to track the number of newly added questions

    for question in questions:
        q = question['question']
        if q not in visited_questions:
            variant_qs = generate_questions(str(QUESTION_VARIANT_PROMPT), q)

            if variant_qs:
                variant_qs["url"] = question["url"]
                question_variants.append(variant_qs)
                visited_questions.add(q)
                count += 1  # Increment the counter for each new question added

                # Save to file every time the count reaches a multiple of 50
                if count % 20 == 0:
                    with open(output_file, 'w') as json_file:
                        json.dump(question_variants, json_file, indent=4)
                    print(f"Intermediate save: wrote #{len(visited_questions)} questions so far")

    # Final save at the end to ensure all questions are written to the file
    with open(output_file, 'w') as json_file:
        json.dump(question_variants, json_file, indent=4)
    print(f"Final save: wrote #{len(visited_questions)} questions")

    return question_variants, visited_questions

def main(input_data_path, output_data_path):
    """
    Main function to generate synthetic question variants.

    Args:
        input_data_path (str): Path to the input JSON file containing questions.
        output_data_path (str): Path to the output JSON file for saving questions.
    """
    if not os.path.exists(input_data_path):
        raise ValueError(f"The input path does not exist: {input_data_path}")
    
    # Load documents from the input JSON file
    with open(input_data_path, 'r') as file:
        questions = json.load(file)
    
    generate_question_variants(questions, output_data_path)


if __name__ == "__main__":
    # python src/eval/synthetic_question_generator.py --input_data_path demos/demo_v0/resources/crawl_data/sellercenter_crawled_data.json  --output_data_path data/sellercenter_question.json

    parser = argparse.ArgumentParser(description="Generate question variants.")

    # Command-line arguments
    parser.add_argument(
        "--input_data_path",
        help="The raw questoin document path (JSON file).",
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