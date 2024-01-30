#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import os
from flask import request, Blueprint

from auth.auth import login_required
from .history_query_form import HistoryQueryForm
from rest.ApiResult import error_message, success
import pandas as pd


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
    # 创建一个空列表，用于存储对象
    objects_list = []
    print(csv_data)
    # 遍历 CSV 数据的每一行，创建对象并添加到列表中
    for index, row in csv_data.iterrows():
        my_object = {
            'open': round(row['Open'],2),
            'high': round(row['High'],2),
            'low': round(row['Low'],2),
            'close': round(row['Close'],2),
            'volume': row['Volume'],
            'timestamp': pd.to_datetime(row['Date']).tz_localize('Asia/Shanghai').timestamp() * 1000,
            'date': row['Date'],
        }
        objects_list.append(my_object)
    
    return success(objects_list)
