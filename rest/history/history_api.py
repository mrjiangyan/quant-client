#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import os
from flask import request, Blueprint

from auth.auth import login_required
from .history_query_form import HistoryQueryForm
from rest.ApiResult import error_message, success
import pandas as pd
from loguru import logger

blueprint = Blueprint(
    'history_api',
    __name__
)


# 获取列表
@login_required
@blueprint.route('/api/history', methods=['GET'])
def get_history(): 
   
    try:
        form = HistoryQueryForm(request.args)
    except Exception as err:
        return error_message(str(err))

    file_path = os.path.join(os.getcwd(), 'resources', 'historical_data', form.period.data, form.symbol.data + '.csv')
    if not os.path.exists(file_path):
        return error_message(f'{file_path}文件不存在')
    csv_data = pd.read_csv(file_path)
    
    # 使用向量化操作将时间戳转换为本地时区并乘以1000
    csv_data['timestamp'] = pd.to_datetime(csv_data['Date']).dt.tz_localize('Asia/Shanghai').view('int64') // 10**6

    # 将数据舍入到两位小数
    csv_data[['open', 'high', 'low', 'close']] = csv_data[['Open', 'High', 'Low', 'Close']].round(2)
    csv_data[['volume','date']] = csv_data[['Volume', 'Date']]
    # 转换为字典并添加到列表中
    objects_list = csv_data.to_dict(orient='records')
    
    return success(objects_list)
