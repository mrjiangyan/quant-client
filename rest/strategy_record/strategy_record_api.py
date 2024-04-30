#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from .strategy_record_query_form import StrategyRecordQueryForm
from .strategy_record_delete_form import StrategyRecordDeleteForm
from .strategy_record_rename_form import StrategyRecordRenameForm
from flask import request, Blueprint
import importlib
import inspect

import os
import platform
import time
from datetime import datetime
import math
import shutil
from auth.auth import login_required
from urllib.parse import unquote
system = platform.system()
 
from rest.ApiResult import error_message, success
from rest.PageResult import PageResult
import re

# 示例：假设策略类定义在名为 "strategies" 的模块中
module_name = "strategy"
summary_file_name = '_summary.log'
strategy_set = set()

def get_all_classes(module_name):
    module = importlib.import_module(module_name)
    all_classes = [obj[1] for obj in inspect.getmembers(module, inspect.isclass) if issubclass(obj[1], object) and obj[1] is not object]
    return all_classes

all_strategies = get_all_classes(module_name)

strategy_objects = []
for index, strategy in enumerate(all_strategies):
    if strategy.__name__ == 'BaseStrategy':
        continue
    strategy_name = getattr(strategy.params, 'name')
    strategy_objects.append({ 'strategy_name':strategy_name, 'strategy': strategy.__name__ })

blueprint = Blueprint(
    'strategy_record_api',
    __name__
)

root_directory = os.getcwd() + '/output'
# 获取策略列表
@login_required
@blueprint.route('/api/strategyRecord/list', methods=['GET'])
def list(): 
    try:
        form = StrategyRecordQueryForm(request.args)
    except Exception as err:
        return error_message(str(err))

    result = recursive_directory_info(root_directory, form)
    
    page_size = form.pageSize.data
    page_no = form.pageNo.data
    offset = get_offset(page_no, page_size)
    
    record_count = len(result)
    if record_count <= offset:
        result = []
    elif record_count < offset+page_size:
        result = result[offset:record_count]
    else:
        result = result[offset:offset+page_size]
    page_result = PageResult(page_no, record_count, page_size, math.ceil(record_count/page_size), result)
    return success(page_result)
   
# 删除策略记录
@login_required
@blueprint.route('/api/strategyRecord', methods=['DELETE'])
def delete():
    try:
        form = StrategyRecordDeleteForm()
    except Exception as err:
        return error_message(str(err))
    shutil.rmtree(form.path.data)
    return success('目录删除成功')


# 修改策略记录任务名称
@login_required
@blueprint.route('/api/strategyRecord/rename', methods=['PUT'])
def rename():
    try:
        form = StrategyRecordRenameForm()
    except Exception as err:
        return error_message(str(err))
    old_directory_name = form.path.data
    if not os.path.exists(old_directory_name):
        return error_message(f'{form.path.data}任务不存在无法进行修改操作')
    new_directory_name = old_directory_name.replace(os.path.basename(old_directory_name), form.taskName.data)
    if os.path.exists(new_directory_name):
            return error_message(f'{form.taskName.data}任务存在, 无法进行修改操作')
    os.rename(old_directory_name, new_directory_name)
    return success('任务名称修改成功')

# 查出该策略记录下面每一只股票的明细
@login_required
@blueprint.route('/api/strategyRecord/detail/list', methods=['GET'])
def quert_detail_by_path():
    path_encoded = None
    try:
        form = StrategyRecordQueryForm()
        path_encoded = request.args.get('path')
        path_decoded = unquote(path_encoded) if path_encoded else None
        if not os.path.exists(path_decoded):
            return error_message(f'{path_encoded}目录不存在')
    except Exception as err:
        return error_message(str(err))
    # 先查出来这一次策略记录的明细，然后根据分页条件差对应页面的记录
    list = recursive_directory_file(path_decoded, form)
    list.sort(key=lambda x: float(x['revenue']), reverse=True)

    result= PageResult(1,len(list),len(list), 1, list)
    return success(result)


@login_required
@blueprint.route('/api/strategyRecord/detail/log', methods=['GET'])
def quert_detail_log():
    path_encoded = None
    try:
        path_encoded = request.args.get('path')
        path_decoded = unquote(path_encoded) if path_encoded else None
        if not os.path.exists(path_decoded):
            return error_message(f'{path_encoded}目录不存在')
    except Exception as err:
        return error_message(str(err))
    #所有的日志
    logs = []
    #记录所有的买入卖出点
    points = []
    buy_date = None
    sell_date = None
    # 先查出来这一次策略记录的明细，然后根据分页条件差对应页面的记录
    with open(path_decoded, 'r') as file:
        for line in file:
            logs.append(line)
            if "买入日期" in line:
                # 解析买入日期和买入价格相关数据
                buy_date = line.split("买入日期: ")[1].split(",")[0]
            elif "买入完成" in line:
                # 解析买入日期和买入价格相关数据
               # 使用正则表达式提取买入价格和买入数量
                buy_price = re.search(r'价格\s+(\d+\.\d+)', line).group(1)
                buy_quantity = re.search(r'数量\s+(\d+)', line).group(1)
                # 创建一个字典存储买入日期和买入价格
                point_data = {
                    'name': 'simpleAnnotation',
                    'extendData': f'买入:{buy_price},数量:{buy_quantity}',
                    'points': [{ 'timestamp': datetime.strptime(buy_date, "%Y-%m-%d").timestamp() * 1000, 'value': float(buy_price) }],
                }
                points.append(point_data)
            if "卖出日期" in line:
                # 解析买入日期和买入价格相关数据
                sell_date = line.split("卖出日期: ")[1].split(",")[0]
            elif "卖出完成" in line:
                # 解析买入日期和买入价格相关数据
               # 使用正则表达式提取买入价格和买入数量
                sell_price = re.search(r'价格\s+(\d+\.\d+)', line).group(1)
                sell_quantity = re.search(r'数量\s*(-\d+)', line).group(1)
                # 创建一个字典存储买入日期和买入价格
                point_data = {
                    'name': 'simpleAnnotation',
                    'extendData': f'卖出:{sell_price}\r\n数量:{sell_quantity}',
                    'points': [{ 'timestamp': datetime.strptime(sell_date, "%Y-%m-%d").timestamp() * 1000, 'value': float(sell_price) }],
                }
                points.append(point_data)
    
    return success({
        'logs' : logs, 'points': points
    })


def get_directory_info(directory):
    stat_result = os.stat(directory)
    if hasattr(stat_result, 'st_birthtime'):
        birthtime = stat_result.st_birthtime
    else:
        # 否则，根据系统选择相似的时间属性
        birthtime = stat_result.st_ctime

    # 初始化目录信息字典
    directory_info = {
        'path': directory,  # 添加完整路径信息
        'name': os.path.basename(directory),
        'create_time': time.strftime('%Y-%m-%d %H:%M', time.localtime(birthtime)),
        'file_count': 0
    }

    # 获取目录中的文件数量
    file_count = 0
    for _, _, files in os.walk(directory):
        file_count += len(files)

    directory_info['file_count'] = 0 if file_count == 0 else file_count-1

    return directory_info

def recursive_directory_file(path, params: StrategyRecordQueryForm):
    summary_path  = os.path.join(path, summary_file_name)
    files_list = []
    # 创建一个空字典，用于存储结果

    data_map = {}  
    if os.path.exists(summary_path):
        # 打开文件并逐行读取内容
        with open(summary_path, 'r') as file:
            for line in file:
                # 如果当前行包含符号 ":"，则进行处理
                if ':' in line:
                    # 使用 split() 方法按 ":" 分割每行，并将结果存储到字典中
                    key, value = line.strip().split(':', 1)  # 使用 maxsplit 参数限制分割次数为 1，防止多个 ":" 导致的错误
                    data_map[key.strip()] = value.strip()

    # 获取指定目录中的所有文件和子目录
    contents = os.listdir(path)
    # 筛选出其中的文件
    for content in contents:
        file = os.path.join(path, content)
        # 判断是否为文件
        if os.path.isfile(file) and file.endswith('.log') and not '_summary' in file:
            file_name_without_extension = os.path.splitext(os.path.basename(file))[0]
            # file_name = os.path.basename(file)  # 获取文件路径的基本文件名
            revenue = 0
            if file_name_without_extension in data_map:
                revenue = data_map[file_name_without_extension]
            files_list.append({'symbol': file_name_without_extension, 'file': file, 'revenue': revenue})
            
    return files_list

def recursive_directory_info(root_directory, params:StrategyRecordQueryForm):
    # 递归遍历指定目录及其子目录，并获取每个目录的信息
    directory_infos = []

    # 获取指定目录中的所有文件和子目录
    contents = os.listdir(root_directory)

    # 筛选出其中的子目录
    subdirectories = [content for content in contents if os.path.isdir(os.path.join(root_directory, content))]

    for root in subdirectories:
        #根据该目录找策略名称
        sub_dir = os.path.join(root_directory, root)
        for dir in os.listdir(sub_dir):
            if not os.path.isdir(os.path.join(sub_dir, dir)):
                continue
            if params.strategy_name.data and params.strategy_name.data not in root:
                continue
            directory_info = get_directory_info(os.path.join(sub_dir, dir))
            directory_info['strategy_name'] = root
            directory_infos.append(directory_info)
         
    # 按照创建时间由近到远进行排序
    directory_infos.sort(key=lambda x: x['create_time'], reverse=True)

    return directory_infos

# 分页查询
def get_offset(page_index, page_size):
    if page_index < 1:
        page_index == 1

    if page_size < 1:
        page_size = 20

    return (page_index - 1) * page_size
