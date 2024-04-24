import numpy as np
import os
import random
import collections
from os.path import dirname, abspath
from copy import deepcopy
from sacred import Experiment, SETTINGS
from sacred.observers import FileStorageObserver, MongoObserver
from sacred.utils import apply_backspaces_and_linefeeds
import sys
import torch as th
from utils.logging import get_logger
import yaml
import subprocess
import time
import psutil
import threading
os.environ['CUDA_VISIBLE_DEVICES'] = "0"

from run import run

SETTINGS['CAPTURE_MODE'] = "fd" # set to "no" if you want to see stdout/stderr in console
logger = get_logger()

ex = Experiment("pymarl")
ex.logger = logger
ex.captured_out_filter = apply_backspaces_and_linefeeds

results_path = os.path.join(dirname(dirname(abspath(__file__))), "results")
# results_path = "/home/ubuntu/data"

@ex.main
def my_main(_run, _config, _log):
    # Setting the random seed throughout the modules
    config = config_copy(_config)
    np.random.seed(config["seed"])
    th.manual_seed(config["seed"])
    config['env_args']['seed'] = config["seed"]

    # run the framework
    run(_run, config, _log)


def _get_config(params, arg_name, subfolder):
    config_name = None
    for _i, _v in enumerate(params):
        if _v.split("=")[0] == arg_name:
            config_name = _v.split("=")[1]
            del params[_i]
            break

    if config_name is not None:
        with open(os.path.join(os.path.dirname(__file__), "config", subfolder, "{}.yaml".format(config_name)), "r") as f:
            try:
                config_dict = yaml.safe_load(f)
            except yaml.YAMLError as exc:
                assert False, "{}.yaml error: {}".format(config_name, exc)
        return config_dict


def recursive_dict_update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = recursive_dict_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def config_copy(config):
    if isinstance(config, dict):
        return {k: config_copy(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [config_copy(v) for v in config]
    else:
        return deepcopy(config)

def is_process_running(process_name):
    # 遍历所有正在运行的进程
    for proc in psutil.process_iter():
        try:
            # 获取进程的名称
            process = psutil.Process(proc.pid)
            name = process.name()
            # 如果找到与目标进程名称匹配的进程，则返回 True
            if name == process_name:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    # 如果未找到匹配的进程，则返回 False
    return False


if __name__ == '__main__':
    print('断点1')
    params = deepcopy(sys.argv)
    print('断点2')
    th.set_num_threads(1)

    # Get the defaults from default.yaml
    with open(os.path.join(os.path.dirname(__file__), "config", "default.yaml"), "r") as f:
        try:
            config_dict = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            assert False, "default.yaml error: {}".format(exc)
    print('断点3')
    # print(params)
    # Load algorithm and env base configs
    env_config = _get_config(params, "--env-config", "envs")
    alg_config = _get_config(params, "--config", "algs")
    
    # config_dict = {**config_dict, **env_config, **alg_config}
    config_dict = recursive_dict_update(config_dict, env_config)
    config_dict = recursive_dict_update(config_dict, alg_config)
    print('断点4')
    try:
        map_name = config_dict["env_args"]["map_name"]
    except:
        map_name = config_dict["env_args"]["key"]    
    
    print('断点5')
    # now add all the config to sacred
    ex.add_config(config_dict)
    
    for param in params:
        if param.startswith("env_args.map_name"):
            map_name = param.split("=")[1]
        elif param.startswith("env_args.key"):
            map_name = param.split("=")[1]
    print('断点6')
    # Save to disk by default for sacred
    logger.info("Saving to FileStorageObserver in results/sacred.")
    file_obs_path = os.path.join(results_path, f"sacred/{map_name}/{config_dict['name']}")
    print('断点7')
    # ex.observers.append(MongoObserver(db_name="marlbench")) #url='172.31.5.187:27017'))
    ex.observers.append(FileStorageObserver.create(file_obs_path))
    # ex.observers.append(MongoObserver())
    print('断点8')

    # 设置一个标志来表示命令行是否正在运行
    commandline_running = False

    def run_experiment():
        global commandline_running
        # 标志为 True 表示命令行正在运行
        commandline_running = True
        # 运行实验命令行
        ex.run_commandline(params)
        # 命令行运行结束后，将标志设置为 False
        commandline_running = False

    # 在另一个线程或异步任务中调用 run_experiment 函数
    

    # 创建一个新的线程来运行实验
    experiment_thread = threading.Thread(target=run_experiment)
    # 启动线程
    experiment_thread.start()

    # while True:
    #     if commandline_running:
    #         print("Command line is running.")
    #     else:
    #         print("Command line is not running.")
    #         break
    #     # time.sleep(2)  # 每隔 1 秒钟检查一次

    # # 检测名为 "ex.run_commandline(params)" 的进程是否正在运行
    # process_name = "ex.run_commandline(params)"
    # is_running = is_process_running(process_name)
    # if is_running:
    #     print(f"Process {process_name} is running.")
    # else:
    #     print(f"Process {process_name} is not running.")
    #     print("Command is running:", is_running)

    print('断点9')
    

    

    
