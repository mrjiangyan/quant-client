#!/usr/bin/python
# -*- coding: UTF-8 -*-
from sqlalchemy import Column, Double, Integer, func, Float, String, Boolean

from data.database import SqlAlchemyBase

from sqlalchemy_serializer import SerializerMixin


class Symbol(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 't_symbols'
    symbol = Column("id", String, primary_key=True)
    market = Column("market", String, index=True, doc="所在市场")
    name = Column("name", String, doc="名称")
    cn_name = Column("cn_name", String, doc="中文名称")
    last_price = Column("last_price", Float,  doc="最后价格")
    ipo_year = Column("ipo_year", Integer, index=True, doc="IPO年份")
    country = Column("country", String, index=True, doc="所属国家")
    industry = Column("industry", String, index=True, doc="所属行业")
    market_cap = Column("market_cap", Integer, index=True, doc="市值")
    volume = Column("volume", Integer,  doc="成交量")
    change_rate = Column("change_rate", Double,  doc="涨跌幅度")
    net_change = Column("net_change", Double,  doc="涨跌金额")
    # 股票数量
    shares_outstanding = Column("shares_outstanding", Integer, doc="总股本")
    short = Column("short", Integer, index=True, doc="是否卖空")
