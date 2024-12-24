import yaml
from typing import Dict


def load_config_dict(path: str):
    with open(path, 'r') as config_file:
        return yaml.full_load(config_file)


def conf_str_to_list(conf_str, convert_type):

    if type(conf_str) == str:
        conf_out = conf_str.split(",")
        conf_out = [convert_type(i) for i in conf_out]
        if convert_type == str:
            conf_out = [i.strip() for i in conf_out]
    else:
        conf_out = [conf_str]

    return conf_out


class GenericConfig:

    def __init__(self, raw: Dict, root: str = '<root>'):
        self.raw = raw
        self.root = root

    def get_man(self, key: str):
        res = self.raw.get(key)
        if res is None:
            raise ValueError("Mandatory configuration property not provided for " + self.root + ": " + key)
        return res

    def get(self, key: str, default=None):
        return self.raw.get(key, default)

    def get_man_gc(self, key: str):
        sub_raw = self.get_man(key)
        new_root = self.root + "." + key
        return GenericConfig(sub_raw, new_root)

    def get_bool(self, key: str):
        return self.raw.get(key, False)

    def to_dict(self):
        return self.raw


class KrylovConfig:
    def __init__(self, root_gc: GenericConfig):
        gc = root_gc.get_man_gc('krylov')

        self.image = gc.get_man('image')
        self.memory = int(gc.get_man('memory'))
        self.cpu_count = int(gc.get_man('cpu_count'))
        self.hadoop_cluster = gc.get('hadoop_cluster')
        self.hadoop_user = gc.get('hadoop_user')
        self.service_account = gc.get('service_account')
        self.gpu_count = gc.get('gpu_count')
        self.gpu_model = gc.get('gpu_model')
        self.default_namespace = gc.get_man('default_namespace')
        self.tess = gc.get("tess")
        self.email_to = gc.get("email_to")
