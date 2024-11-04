#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# flake8: noqa

import os
import yaml


# 获取应用程序的根目录
def get_root_directory():
    current_dir = os.path.abspath(__file__)  # Get the absolute path of the current file
    while not os.path.isfile(os.path.join(current_dir, 'config.yaml')):
        # Check if a marker file exists in the current directory
        current_dir = os.path.dirname(current_dir)  # Move up one directory
        if current_dir == '/':  # Stop if we have reached the root directory
            break
    return current_dir


root_directory = get_root_directory()
# 构建配置文件的完整路径
config_path: str = os.path.join(root_directory, 'config.yaml')


def read_config(key: str) -> str:
    # 读取 YAML 配置文件
    with open(file=config_path, mode='r') as f:
        config = yaml.safe_load(stream=f)
        return config.get(key, None)
