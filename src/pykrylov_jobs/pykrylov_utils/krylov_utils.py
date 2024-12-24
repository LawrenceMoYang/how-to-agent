import os
import pathlib
from collections import OrderedDict
from typing import List
from setuptools import find_packages
import datetime
import time

import pykrylov as kry
from pykrylov.trigger import condition, EmailAction
from pykrylov.util.error import PyKrylovError

from src.pykrylov_jobs.pykrylov_utils.krylov_config import GenericConfig, KrylovConfig

def mkdir_quiet(path: str):
    pathlib.Path(path).mkdir(exist_ok=True, parents=True)


def print_time() -> str:
    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

class Krylovizator:

    def __init__(self, root_gc: GenericConfig):
        self.conf = KrylovConfig(root_gc)
        kry.util.switch_krylov(self.conf.tess)

    def submit_job(self, task_object, task_args: List, task_num=1, namespace: str = None, project_name: str = None
                   , schedule: str = None) -> str:

        if not namespace:
            namespace = self.conf.default_namespace

        if self.conf.gpu_count:
            gpu_count = int(self.conf.gpu_count)
        else:
            gpu_count = None

        workflow = OrderedDict()
        for i in range(task_num):
            task = kry.Task(
                task_object=task_object,
                args=task_args,
                docker_image=self.conf.image,
                gpu=gpu_count
            )

            task.add_memory(self.conf.memory)
            task.add_cpu(self.conf.cpu_count)

            if gpu_count:
                task.run_on_gpu(quantity=int(gpu_count), model=self.conf.gpu_model)

            if self.conf.hadoop_user:
                task.run_on_hadoop(cluster=self.conf.hadoop_cluster, batch_user=self.conf.hadoop_user)
            packages = find_packages()
            task.add_packages(packages)

            workflow[task] = []

        if self.conf.email_to:
            workflow = kry.Flow(workflow)

            workflow.add_trigger(
                condition.ON_WORKFLOW_TERMINATED,
                EmailAction([self.conf.email_to])
            )

        session = kry.Session(namespace=namespace)
        self._switch_to_account(namespace=namespace)
        if project_name:
            if schedule:
                exp_id = session.submit_experiment(workflow, project_name, schedule=schedule)
                print(f"Experiment ID: {exp_id}")
                print(f"AIHUB link: https://94.aihub.krylov.vip.ebay.com/projects/{project_name}/experiments/{exp_id}")
                return exp_id
            else:
                exp_id = session.submit_experiment(workflow, project_name)
                experiment = kry.ems.show_experiment(exp_id)
                run_id = experiment['runtime']['workflow']['runId']
                print(f"Experiment ID: {exp_id}")
                print(f"Run ID: {run_id}")
                print(f"AIHUB link: https://94.aihub.krylov.vip.ebay.com/projects/{project_name}/experiments/{exp_id}")
                return exp_id
        else:
            return session.submit(workflow)

    def create_task(self, task_object, task_args, conf: KrylovConfig = None):
        if not conf:
            conf = self.conf

        gpu_count = conf.gpu_count
        # krylov won't accept 0
        if gpu_count == 0:
            gpu_count = None
        task = kry.Task(
            task_object=task_object,
            args=task_args,
            docker_image=conf.image,
            gpu=gpu_count
        )
        task.add_memory(conf.memory)
        task.add_cpu(conf.cpu_count)
        if gpu_count:
            task.run_on_gpu(quantity=int(gpu_count), model=conf.gpu_model)
        if self.conf.hadoop_user:
            task.run_on_hadoop(cluster=conf.hadoop_cluster, batch_user=conf.hadoop_user)
        self._add_python_packages(task)
        # for dir in conf.extra_dirs:
        #     self._add_python_packages(task, dir)
        return task

    def submit(self, task_or_workflow, namespace: str = None):
        if not namespace:
            namespace = self.conf.default_namespace

        self._switch_to_account(namespace)
        session = kry.Session(namespace=namespace)
        try:
            return session.submit(task_or_workflow)
        except PyKrylovError as e:
            if 'session has expired' in e.args[0]:
                session.login()
                return session.submit(task_or_workflow)
            else:
                raise e

    def _switch_to_account(self, namespace):
        sa = self.conf.service_account
        if sa:
            print(f"Switching to service account {sa}, namespace {namespace}")
            kry.util.config.use_account(
                account_name=sa,
                namespace=namespace,
                yubikey_required=False
            )

    @staticmethod
    def _add_python_packages(task, dir='.'):
        packages = find_packages(where=dir)
        for package in packages:
            print("Adding package:", package, ' -> ', os.path.join(dir, *package.split(".")))
            task.add_package(package, os.path.join(dir, *package.split(".")))


class KryEnv:
    @staticmethod
    def data_dir() -> str:
        return os.getenv('KRYLOV_DATA_DIR')

    @staticmethod
    def user_dir() -> str:
        return os.getenv('KRYLOV_WF_PRINCIPAL')

    @staticmethod
    def transformers_cache_dir():
        if os.getenv('KRYLOV_DATA_DIR'):
            dd = f'{KryEnv.data_dir()}/{KryEnv.user_dir()}'
            res = f'{dd}/transformers_cache'
            mkdir_quiet(res)
            return res
        return None

    @staticmethod
    def tmp_dir_base():
        dd = f'{KryEnv.data_dir()}/{KryEnv.user_dir()}'
        tmp = f'{dd}/tmp'
        mkdir_quiet(tmp)
        return tmp

