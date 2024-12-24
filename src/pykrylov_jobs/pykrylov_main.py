import argparse
import json

from src.pykrylov_jobs.index_builder.run_index_builder import IndexBuilder
from src.pykrylov_jobs.pykrylov_utils.krylov_config import GenericConfig, load_config_dict
from src.pykrylov_jobs.pykrylov_utils.krylov_utils import Krylovizator


def run_index_builder(gc_ser: str):
    dict_obj = json.loads(gc_ser)
    root_gc = GenericConfig(dict_obj)

    IndexBuilder(root_gc)


def main():
    tasks_dict = {"index_builder": run_index_builder}

    parser = argparse.ArgumentParser()
    parser.add_argument('--task', type=str, help='task type', required=True, choices=tasks_dict.keys())
    parser.add_argument('--config-path', type=str, help='config file', required=True)
    parser.add_argument('--project-name', type=str, help='project name', required=True, default="how-to-agent")
    parser.add_argument('--service-account', type=str, help='service account', required=False)

    args = parser.parse_args()

    config_dict = load_config_dict(args.config_path)

    if args.service_account:
        if not config_dict["krylov"].get("service_account"):
            config_dict["krylov"]["service_account"] = args.service_account

    root_gc = GenericConfig(config_dict)
    gc_ser = json.dumps(root_gc.to_dict())
    kry = Krylovizator(root_gc)
    task_args = [gc_ser]

    assert args.task in tasks_dict.keys(), f"{args.task} is not a supported task, select one of {tasks_dict.keys()}"

    kry.submit_job(task_object=tasks_dict[args.task], task_args=task_args, project_name=args.project_name)

    print(f"Job launched successfully.")


if __name__ == "__main__":
    main()
