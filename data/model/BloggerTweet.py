#!/usr/bin/python3
# -*- coding: UTF-8 -*-


import sqlalchemy
from data.database import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy import Column, Integer, String, Text, DateTime


class BloggerTweet(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 't_blogger_tweets'

    id = sqlalchemy.Column(sqlalchemy.String(256), primary_key=True, doc="id")
    blogger_id = Column(Integer)  # 博主的ID
    content = Column(Text)          # 文章内容
    image_url = Column(String(255))  # 推文相关图片
    symbol = Column(String(64))  # 推文关键字
    published_at = Column(DateTime, nullable=False)  # 推文发布时间
    favorite_count = Column(Integer)  # 点赞数量
    reply_count = Column(Integer)  # 回复数量
    retweet_count = Column(Integer)  # 引用数量
    bookmark_count = Column(Integer)  # 收藏标签数量
    url = Column(String(255))  # 推文原始链接
