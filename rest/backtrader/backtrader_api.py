#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import os
from flask import Blueprint

from auth.auth import login_required
from .backtrader_form import BackTraderForm
from rest.ApiResult import error_message, success
import threading
from run_stretegy import run_strategy
from concurrent.futures import ThreadPoolExecutor
# 创建一个线程池
executor = ThreadPoolExecutor(max_workers=2)

blueprint = Blueprint(
    'backtrader_api',
    __name__
)


# 获取列表
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
    # StrategyThread(symbols, strategy, period , days).start()
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