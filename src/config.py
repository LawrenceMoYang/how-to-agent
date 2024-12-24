# General Configuration
SELLER_CONTENT_PATH = "demos/demo_v0/resources/content/sellercenter_crawled_data.json"
HELP_GUIDES_CONTENT_PATH = "demos/demo_v0/resources/content/help_guides_data.json"
HELP_GUIDES_RAW_PATH = "../../data/help_guides/en_US.json"

INDEX_PATH = "demos/demo_v0/resources/indexes"

EMBEDDER_MODELS = {"MPNet-V2":
                       {"model_name": "sentence-transformers/all-mpnet-base-v2",
                        "index_path": f"{INDEX_PATH}/mpnet_index.pkl",
                        "chunk_size": 384},
                   "Vector-Prime":
                       {"model_name": "EBAY_INTERNAL_VECTOR_PRIME",
                        "index_path": f"{INDEX_PATH}/vector_prime_index.pkl",
                        "chunk_size": 384}
                   }

CHAT_MODELS = {"GPT4-Turbo": "azure-chat-completions-gpt-4-turbo-2024-04-09",
               "LLaMa3-70B": "ebay-internal-chat-completions-sandbox-llama-3-70b-instruct",
               "Phi-3-5": "ebay-internal-chat-completions-phi-3-5-mini-instruct",
               "LLaMa3-8B": "ebay-internal-chat-completions-sandbox-llama-3-8b-instruct"
               }

# Crawling.
SRC_URL_FOR_SELLER_HOWTO = "https://www.ebay.com/sellercenter/selling"
CONTENT_PATH = "../../demos/demo_v0/resources/content"