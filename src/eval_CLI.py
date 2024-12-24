import argparse
import sys
import os
import json
import logging

# Add the parent directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))



class EvalCLI(object):
    """
    CLI for interacting with evaluation models. Supported commands:
    - generate_questions: Generate synthetic questions from documents.
    - generate_question_variants: Extend synthetic questions into variants.
    - evaluate_retrieval: Evaluate retrieval models using synthetic and variant questions.
    """

    def __init__(self, sys_args):
        parser = argparse.ArgumentParser(
            description="Evaluation model runner CLI",
            usage='''cli.py <command> [<args>]
       Available sub-commands:
            generate_questions           Generate synthetic questions from documents
            generate_question_variants   Extend synthetic questions into variants
            evaluate_retrieval           Evaluate retrieval models
        ''')
        parser.add_argument('command', help='Subcommand to run')
        parser.add_argument("--config_file_path", default="", help="Path to the configuration file")
        parser.add_argument("--experiment_name", default="", help="the experiment to run")
        parser.add_argument("--output_path", help="Path to save the results")
        parser.add_argument("--enable_evaluate_variants", action="store_true", default=False, help="Enable evaluation with extended questions (default: False)")
        
        args = parser.parse_args(sys_args[0:1])

        if not hasattr(self, args.command):
            print(f'Unrecognized command: {args.command}')
            parser.print_help()
            exit(1)

        command_args = sys_args[1:]

        command_args = parser.parse_args(sys_args)
        config_file_path = command_args.config_file_path
        experiment_name = command_args.experiment_name
        evaluate_variants = command_args.enable_evaluate_variants

        if not config_file_path:
            # Get the full path of the current file
            current_file_path = os.path.abspath(__file__)
            config_file_path = os.path.abspath(os.path.join(current_file_path, "../../data/eval/config.json"))

        experiments_config, output_path = self.load_configuration(config_file_path)

        if experiment_name:
            experiments_config = [config for config in experiments_config if config["experiment_name"] == experiment_name]

        getattr(self, args.command)(experiments_config, output_path=output_path, evaluate_variants=evaluate_variants)


    def load_configuration(self, config_file_path):
        assert os.path.exists(config_file_path), "the current file did not exited"

        with open(config_file_path, "r") as f:
            config = json.load(f)

        output_base_path = os.path.join(os.path.dirname(config_file_path), "output")
      
        experiments = []
        for expr_name, expr_config in config["exps"].items():
            assert "document_path" in expr_config, "the document path is required"
            
            document_path = expr_config["document_path"]
            cache_question_emb = expr_config.get("cache_question_emb", False)

            expr_dir = os.path.join(output_base_path, expr_name)
            output_path = os.path.join(output_base_path, f"result.json")
            if not os.path.exists(expr_dir):
                os.makedirs(expr_dir)

            index_cache_path = os.path.join(os.path.expanduser("~"), ".cache", "how_to_agent/index")
            if not os.path.exists(index_cache_path):
                os.makedirs(index_cache_path)

            if "variants" not in expr_config:
                variants = [{
                    "chunk_size", 384,
                    "model_name", "MPNet-V2"
                }]
            else:
                variants = expr_config["variants"]

            for variant in variants:

                chuck_size = variant.get("chunk_size", 384)
                model_name = variant.get("model_name", "MPNet-V2")

                if "index_file_path" in variant:
                    index_file_path =  variant["index_file_path"]
                else:
                    index_file_path = os.path.join(index_cache_path, f"{expr_name}_{model_name}_{chuck_size}_index.pkl")
                generate_question_path = os.path.join(expr_dir, f"questions.json")
                question_variant_path = os.path.join(expr_dir, f"question_variants.json")
                question_emb_cach_path = os.path.join(expr_dir, f"{model_name}_question_emb.pkl")
                question_variant_emb_cach_path = os.path.join(expr_dir, f"{model_name}_question_variant_emb.pkl")
               

                experiments.append({
                    "experiment_name": expr_name,
                    "document_path": document_path,
                    "index_model_name": model_name,
                    "chuck_size": chuck_size,
                    "index_file_path": index_file_path,
                    "generate_question_path": generate_question_path,
                    "question_variant_path": question_variant_path,
                    "question_emb_cach_path": question_emb_cach_path if cache_question_emb else None,
                    "question_variant_emb_cache_path": question_variant_emb_cach_path if cache_question_emb else None,
                    "output_path": output_path
                })

        return experiments, output_path
    
    def generate_question_variants(self, experiments_config, **args):
        
        from src.eval.llm_question_extension import main
        for experiment in experiments_config:
            main(experiment["generate_question_path"], experiment["question_variant_path"])


    def generate_questions(self, experiments_config, **args):
        from src.eval.synthetic_question_generator import main
        for experiment in experiments_config:
            main(experiment["document_path"], experiment["generate_question_path"])

    def evalate_retrieval(self, experiments_config, output_path=None, evaluate_variants=False):

        # questions_path, document_path, chunk_index_path, top_k=5, chunk_size=384, index_model_name='MPNet-V2', question_emb_cach_path=None
        
        result = []
        for experiment_index, experiment in enumerate(experiments_config, start=1):
            print(f"--- Starting Experiment {experiment_index}/{len(experiments_config)} ---")
        
            from src.eval.synthetic_question_generator import main as question_generator
            from src.eval.retrieval_evaluation import main as retrieval_evaluation
            from src.eval.llm_question_extension import main as question_extension

            # Step 1: Generate synthetic questions
            print(f"[Step 1] Generating synthetic questions for {experiment['document_path']}")
            question_generator(experiment["document_path"], experiment["generate_question_path"])
            print(f"[Step 1 Completed] Synthetic questions saved to {experiment['generate_question_path']}\n")

            

            # Step 3: Evaluate with synthetic questions
            print("[Step 2] Evaluating retrieval with synthetic questions...")
            hit_rate, mAP = retrieval_evaluation(questions_path=experiment["generate_question_path"], 
                                 document_path=experiment["document_path"], 
                                 chunk_index_path=experiment["index_file_path"],
                                 chunk_size=experiment["chuck_size"],
                                 index_model_name=experiment["index_model_name"],
                                 question_emb_cach_path=experiment["question_emb_cach_path"])
            print(f"[Step 2 Completed] Metrics: hit_rate={hit_rate}, mAP={mAP}\n")

            expr_result = {
                    "chunk_size": experiment["chuck_size"],
                    "metrics":{
                        "hit_rate": hit_rate,
                        "mAP": mAP
                    }
                }

            if evaluate_variants:
                # Step 2: Extend questions
                print(f"[Step 3] Extending questions in {experiment['generate_question_path']}")
                question_extension(experiment["generate_question_path"], experiment["question_variant_path"])
                print(f"[Step 3 Completed] Extended questions saved to {experiment['question_variant_path']}\n")

                
                print(f"[Step 4] Evaluating retrieval with variant questions...")
                variant_hit_rate, variant_mAP = retrieval_evaluation(experiment["question_variant_path"], 
                                    document_path=experiment["document_path"], 
                                    chunk_index_path=experiment["index_file_path"],
                                    chunk_size=experiment["chuck_size"],
                                    index_model_name=experiment["index_model_name"],
                                    question_emb_cach_path=experiment["question_variant_emb_cache_path"],
                                    question_type="variant")
                print(f"[Step 4 Completed] Metrics: variant_hit_rate={variant_hit_rate}, variant_mAP={variant_mAP}\n")

                expr_result["metrics"]["variant_hit_rate"] = variant_hit_rate
                expr_result["metrics"]["variant_mAP"] = variant_mAP

            
            result.append(expr_result)

            print((f"--- Experiment {experiment_index} Completed ---\n")
)

        with open(output_path, 'w') as json_file:
            json.dump(result, json_file, indent=4)

        print(f"Results saved successfully to {output_path}")


# input_data_path, output_data_path
def main():
    EvalCLI(sys.argv[1:])
   
    
if __name__ == "__main__":
    main()