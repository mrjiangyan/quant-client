#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from flask import request, jsonify
import flask

from auth.auth import login_required

from rest.ApiResult import success, error_message
from data.model.t_symbol import Symbol
from data.service.symbol_service import get_by_symbol
from data import database
blueprint = flask.Blueprint(
    'dict_api',
    __name__
)




# 获取业务引擎列表
@login_required
@blueprint.route('/api/dict/<string:column>', methods=['GET'])
def dict(column:str): 
    if not column:
        return error_message('字段名是必须的')

    with database.create_database_session() as db_sess:   
        from sqlalchemy import select
        query = select(*[getattr(Symbol, column)]).distinct().select_from(Symbol)
        # 执行查询并获取结果
        result = db_sess.execute(query).fetchall()
        # 将结果转换为 JSON 格式
        distinct_values = [{'value': row[0], 'text': row[0]} for row in result]
        distinct_values.sort(key=lambda x: str(x['text']), reverse=False)

    return success(distinct_values)

