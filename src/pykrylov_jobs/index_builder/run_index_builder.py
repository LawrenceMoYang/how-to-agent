import os
import pathlib
from src.docindex import DocIndex
from src.pykrylov_jobs.pykrylov_utils.krylov_config import GenericConfig
from src.pykrylov_jobs.pykrylov_utils.krylov_utils import print_time, KryEnv

_DEFAULT_VECTOR_PRIME_PATH = "data/ebay/data/gfuchs/LLMs/vector_prime_tokenizer"

class IndexBuilderConfig:

    def __init__(self, root_gc: GenericConfig):
        gc = root_gc.get_man_gc('index_builder')

        self.input_data = gc.get_man('input_data')
        self.seller_center_data = gc.get_man("seller_center_data")
        self.help_guides_data = gc.get_man("help_guides_data")
        self.output_path = gc.get_man('output_path')
        self.embedder_path_or_name = gc.get_man("embedder_path_or_name")
        self.chunk_size = int(gc.get_man("chunk_size"))
        self.dev_mode = gc.get_bool("dev_mode")
        self.vector_prime_tokenizer_path = gc.get("vector_prime_tokenizer_path")


def get_embedder_param(embedder_path_or_name: str, output_dir: str) -> dict:

    assert 'mpnet' in embedder_path_or_name or 'EBAY_INTERNAL_VECTOR_PRIME' in embedder_path_or_name, \
        f"Invalid embedder path or name: {embedder_path_or_name}"
    if 'mpnet' in embedder_path_or_name:
        embedder_path_or_name = os.path.join(KryEnv.data_dir(), KryEnv.user_dir(), embedder_path_or_name)
        index_output_dir = os.path.join(output_dir, 'mpnet_index.pkl')
    elif 'EBAY_INTERNAL_VECTOR_PRIME' in embedder_path_or_name:
        index_output_dir = os.path.join(output_dir, 'vector_prime_index.pkl')

    return {'embedder_path_or_name': embedder_path_or_name, 'index_output_dir': index_output_dir}


class IndexBuilder:

    def __init__(self, root_gc: GenericConfig):
        print(f"Index builder script starting, time: {print_time()}")

        conf = IndexBuilderConfig(root_gc)
        print(f"config={conf.__dict__}")

        kry_data_dir = os.path.join(KryEnv.data_dir(), KryEnv.user_dir())
        input_dir = os.path.join(KryEnv.data_dir(), conf.input_data)
        seller_center_data = os.path.join(input_dir, conf.seller_center_data)
        help_guides_data = os.path.join(input_dir, conf.help_guides_data)
        output_dir = os.path.join(kry_data_dir, conf.output_path, f"chunk_size_{conf.chunk_size}")
        pathlib.Path(output_dir).mkdir(exist_ok=True, parents=True)

        embedder_details = get_embedder_param(conf.embedder_path_or_name, output_dir)

        vector_prime_tokenizer_path = conf.vector_prime_tokenizer_path or _DEFAULT_VECTOR_PRIME_PATH

        doc_index = DocIndex(vector_prime_tokenizer_path=vector_prime_tokenizer_path)
        doc_index.build(
            content_paths=[seller_center_data, help_guides_data],
            index_path=embedder_details['index_output_dir'],
            embedder_model_name=embedder_details['embedder_path_or_name'],
            chunk_size=conf.chunk_size,
            dev=conf.dev_mode
        )

        print(f"Script is done, time: {print_time()}")











