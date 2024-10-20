#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import os
from flask import Blueprint

from auth.auth import login_required
from .backtrader_form import BackTraderForm, BackTraderRetryForm
from rest.ApiResult import error_message, success
import threading
from run_stretegy import run_strategy
from concurrent.futures import ThreadPoolExecutor
dict_keywords = ['symbols', 'days', 'period', 'strategy']


# 创建一个线程池
executor = ThreadPoolExecutor(max_workers=2)

blueprint = Blueprint(
    'backtrader_api',
    __name__
)



# 回测某一个记录
@login_required
@blueprint.route('/api/backtrader', methods=['POST'])
def create_backtrader(): 
    try:
        form = BackTraderForm()
    except Exception as err:
        return error_message(str(err))
    symbols = form.symbols.data
    strategy = form.strategy.data
    period = form.period.data
    days = form.days.data
    future = executor.submit(run_strategy, symbols, period, days, strategy )
    return success(message='回测任务提交成功，请等待回测完成')

# 根据已有的回测记录进行回测
@login_required
@blueprint.route('/api/backtrader/retry', methods=['POST'])
def retry_backtrader(): 
    try:
        form = BackTraderRetryForm()
    except Exception as err:
        return error_message(str(err))
    #找到已有的记录目录，根据文件名找到所有的股票代码
    #根据已有的目录名称找到策略配置
    if not os.path.exists(form.path.data):
        return error_message(f'{form.path}目录不存在无法进行回测')
    summary_path = form.path.data + '/_summary.log'
    if not os.path.exists(summary_path):
        return error_message(f'{summary_path}文件不存在无法进行回测')
    
    with open(summary_path, 'r') as file:
        # 用列表推导式过滤不包含指定关键字的键值对，并存储到字典中
        data_map = {key.strip(): value.strip() for line in file if ':' in line for key, value in [line.strip().split(':', 1)] if all(keyword in key.strip() for keyword in dict_keywords)}
                    

    symbols = data_map['symbols']
    strategy = data_map['strategy']
    period = data_map['period']
    days = data_map['days']
    future = executor.submit(run_strategy, symbols, period, days, strategy )
    return success(message='回测任务提交成功，请等待回测完成')


# 定义一个简单的线程类
class StrategyThread(threading.Thread):
    def __init__(self, symbols, strategy, period, days):
        super().__init__()
        self.symbols = symbols
        self.strategy = strategy
        self.period = period
        self.days = days
    
    def run(self):
        print(f"Starting {self.strategy}")
        # 设置线程优先级
        os.nice(10)  # 这里的参数值可以根据需求进行调整
        run_strategy(self.symbols, self.period, self.days, self.strategy)
        print(f"Exiting {self.strategy}")