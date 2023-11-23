#!/usr/bin/python
# -*- coding: UTF-8 -*-
from sqlalchemy import Column, DateTime,Integer, func, Float, String

from data.database import SqlAlchemyBase

from sqlalchemy_serializer import SerializerMixin

# 条件选股选中的股票
class SymbolCondition(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 't_symbol_condition'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column("symbol", String, index=True)
    market = Column("market", String, index=True, doc="所在市场")
    condition = Column("condition", String, doc="选股条件")
    gmtUpdate = Column("gmt_update", DateTime, default=func.now(), onupdate=func.now(), doc="更新时间")
   
    
