#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import math
from flask import request, Blueprint
from sqlalchemy import or_
from sqlalchemy import asc, desc

from auth.auth import login_required
from data import database
from .symbol_query_form import SymbolQueryForm
from .symbol_form import SymbolModifyForm
from data.model.t_symbol import Symbol
from data.service.symbol_service import get_by_symbol
from rest.ApiResult import ApiResult, error_message, success

blueprint = Blueprint(
    'symbol_api',
    __name__
)


# 获取列表
@login_required
@blueprint.route('/api/symbol/list', methods=['GET'])
def list(): 
    try:
        form = SymbolQueryForm(request.args)
    except Exception as err:
        return error_message(str(err))

    db_sess = database.create_session()

    symbol_query = db_sess.query(Symbol)

    filterList = []

    if form.symbol.data:
        filterList.append(Symbol.symbol == form.symbol.data )
    if form.keyword.data:
        filterList.append(or_(Symbol.name.like(f'%{form.keyword.data}%'), Symbol.symbol.like(f'%{form.keyword.data}%')))
    if form.market.data is not None:
        filterList.append(Symbol.market == form.market.data  )
    if form.country.data is not None:
        filterList.append(Symbol.country== form.country.data )

    page_size = form.pageSize.data
    page_no = form.pageNo.data
    offset = get_offset(page_no, page_size)
    if form.order.data == 'asc':
        sort_expression = asc(getattr(Symbol, form.column.data))
    else:
        sort_expression = desc(getattr(Symbol, form.column.data))

    record_list = symbol_query.filter(*filterList).order_by(sort_expression).offset(offset).limit(form.pageSize.data).all()

    record_count = symbol_query.filter(*filterList).count()

    page_result = {
        "current": page_no,
        "total": record_count,
        "size": page_size,
        "pages": math.ceil(record_count/page_size),
        "records": [item.to_dict() for item in record_list]
    }
    return success(page_result)

# 查询单个信息
@login_required
@blueprint.route('/api/symbol/<string:symbol>/<string:market>', methods=['GET'])
def get_symbol(symbol, market):
    db_sess = database.create_session()

    symbol = get_by_symbol(db_sess, symbol, market)

    if symbol is None:
        return error_message(f'不存在该symbol:{symbol}')
    return success(symbol.to_dict())

# 屏蔽
@login_required
@blueprint.route('/api/symbol/disable', methods=['PUT'])
def disable(): 
    try:
        form = SymbolModifyForm().validate_for_api()
    except Exception as err:
        return error_message(str(err))

    db_sess = database.create_session()

    symbol = get_by_symbol(db_sess, form.symbol.data, form.market.data)

    if symbol is None:
        return error_message(f'不存在该symbol:{form.symbol.data}')
    
    symbol.compute = False
    db_sess.merge(symbol)
    db_sess.commit()
    return success(message='屏蔽成功')

# 取消屏蔽
@login_required
@blueprint.route('/api/symbol/enabled', methods=['PUT'])
def enable(): 
    try:
        form = SymbolModifyForm().validate_for_api()
    except Exception as err:
        return error_message(str(err))

    db_sess = database.create_session()

    symbol = get_by_symbol(db_sess, form.symbol.data, form.market.data)

    if symbol is None:
        return error_message(f'不存在该symbol:{form.symbol.data}')
    
    symbol.compute = True
    db_sess.merge(symbol)
    db_sess.commit()
    return success(message='取消屏蔽成功')
    
# 进行编辑操作
@login_required
@blueprint.route('/api/symbol', methods=['PUT'])
def update(): 
    try:
        form = SymbolModifyForm().validate_for_api()
    except Exception as err:
        return error_message(str(err))

    db_sess = database.create_session()

    symbol = get_by_symbol(db_sess, form.symbol.data, form.market.data)

    if symbol is None:
        return error_message(f'不存在该symbol:{form.symbol.data}')
    
    print(symbol)
    symbol.cn_name = form.cn_name.data
    print(symbol.cn_name)
    db_sess.merge(symbol)
    db_sess.commit()
    return success(message='编辑成功')
    
   
    

# 分页查询
def get_offset(page_index, page_size):
    if page_index < 1:
        page_index == 1

    if page_size < 1:
        page_size = 20

    return (page_index - 1) * page_size
