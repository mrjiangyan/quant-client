#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import sqlalchemy
from data.database import SqlAlchemyBase
from sqlalchemy import Column, Integer, String


class Blogger(SqlAlchemyBase):
    __tablename__ = 't_bloggers'

    id = sqlalchemy.Column(Integer, primary_key=True, doc="id")
    username = Column(String(32))  # 用户名
    x_id = Column(String(32))  # x_id
