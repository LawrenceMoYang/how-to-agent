
# README: Evaluation Framework for Retrieval-Augmented Generation (RAG)

We have developed a systematic evaluation framework for Retrieval-Augmented Generation (RAG) tailored to the "How-to Age" project. The framework evaluates two critical performance dimensions:

- **Retrieval Quality**: Measures the system's ability to retrieve relevant document chunks in response to user queries.
- **Answer Generation Quality**: Assesses the accuracy, relevance, fluency, and completeness of the generated answers based on retrieved chunks.

This guide outlines the steps required to run the evaluation.

---

### 1. Define the Evaluation Task

To begin, configure the evaluation task by editing the file `data/output/config.json`. Below is an example configuration:

```json
{
    "settings": {
        "output_path": "../eval"
    },
    "exps": {
        "seller_center": {
            "document_path": "demos/demo_v0/resources/content/sellercenter_crawled_data.json",
            "cache_question_emb": false,
            "variants": [
                {
                    "model_name": "MPNet-V2",
                    "chunk_size": 384
                }
            ]
        },
       ....
    }
}
```

#### Configuration Details

- **Experiment Name**: Each experiment (e.g., `seller_center`, `help_guides`) must be defined with the following fields:
  - **`document_path`**: Path to the raw document data for the experiment.
  - **`cache_question_emb`**: Boolean flag to enable/disable caching of synthetic question embeddings.
  - **`variants`**: Specifies the experiment variants:
    - **`model_name`**: Name of the model used for sentence embeddings.
    - **`chunk_size`**: Size of the chunks used in the RAG process.

---

### 2. Start the Evaluation

Run the evaluation using the following command:

```bash
python src/eval_CLI.py [COMMAND] [arguments]
```

#### Commands

- **`generate_questions`**: Generate synthetic questions from the documents.
- **`generate_question_variants`**: Create variants of the synthetic questions.
- **`evaluate_retrieval`**: Evaluate retrieval model results. This command also runs `generate_questions` and `generate_question_variants`.

#### Arguments

- **`--experiment_name`**: Specify the name of the experiment to run, as defined in the configuration file. If not provided, all experiments will be executed.
- **`--enable_evaluate_variants`**: Boolean flag to enable evaluation of question variants. Default is `false`.

---

### Example Usage

To generate synthetic questions for the `seller_center` experiment:

```bash
python src/eval_CLI.py generate_questions --experiment_name seller_center
```

To evaluate retrieval performance for all experiments with question variant evaluation enabled:

```bash
python src/eval_CLI.py evaluate_retrieval --enable_evaluate_variants true
```

---

This framework provides a structured approach to assessing both retrieval and answer generation quality in RAG systems. Modify the configuration and commands to suit your specific evaluation needs.
