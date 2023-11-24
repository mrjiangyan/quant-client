#!/usr/bin/python
# -*- coding: UTF-8 -*-
from sqlalchemy import Column, DateTime,Integer, func, Float, String

from data.database import SqlAlchemyBase

from sqlalchemy_serializer import SerializerMixin


class Symbol(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 't_symbols'

    symbol = Column("symbol", String, primary_key=True)
    market = Column("market", String, index=True,doc="所在市场")
    name = Column("name", String, doc="名称")
    last_price = Column("last_price", Float,  doc="最后价格")
    ipo_year = Column("ipo_year", Integer, index=True, doc="IPO年份")
    country = Column("country", String, index=True, doc="country")
    industry = Column("industry", String, index=True, doc="所属行业")
    market_cap = Column("market_cap", Integer, index=True, doc="市值")
    volume = Column("volume", Integer, index=True, doc="成交量")

    
    
    # imdb_link = Column("imdb_link", String, index=True, doc="imdb_link")
    # douban_link = Column("douban_link", String, index=True, doc="douban_link")
    # category = Column("category", String, index=True, doc="category")
    
    # cover = Column("cover", String, doc="封面图片地址")
    # images = Column("images", String, doc="介绍图片地址")
    # torrent = Column("torrent", String, doc="种子地址,用‘,'来','分割多个地址")
    # unicode = Column("unicode", String, index=True, doc="唯一标识")
   
    gmtUpdate = Column("gmt_update", DateTime, default=func.now(), onupdate=func.now(), doc="更新时间")
   
    
