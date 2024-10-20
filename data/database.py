#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec
from loguru import logger
from contextlib import contextmanager

# 创建全局的Base类
SqlAlchemyBase = dec.declarative_base()

__factory = None  # 作为全局的 session 工厂
__db_file = None  # 用于存储数据库文件路径

__db_user = 'root'
__db_pass = '1qaz%40WSX3edc%24RFV'
__db_host = '192.168.118.74:30772'
__db_name = 'quant'

conn_str = f'mysql+pymysql://{__db_user}:{__db_pass}@{__db_host}/{__db_name}?charset=utf8mb4'
   

def global_init():
    global __factory
    global __db_file

    if __factory:
        return

    logger.info(f"Connection String {conn_str}")

    # 创建数据库引擎，连接到MySQL
    engine = sa.create_engine(
        conn_str,
        echo=True,
        pool_size=20,         # 数据库连接池初始化的容量
        max_overflow=10,      # 连接池最大溢出容量
        pool_recycle=360,     # 重连周期
    )

    # 创建Session工厂
    __factory = orm.sessionmaker(bind=engine)

    # 创建所有表结构
    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()

@contextmanager
def create_database_session():
    # 在这里打开数据库连接
    db_sess = create_session()
    try:
        yield db_sess
    finally:
        # 在这里关闭数据库连接
        db_sess.close()


def create_readonly_session() -> Session:
    global __db_file
    if not __db_file:
        raise Exception("Database file is not initialized")

    engine = sa.create_engine(conn_str, echo=True)

    # 创建会话工厂
    Session = orm.sessionmaker(bind=engine)

    # 创建只读会话
    session = Session()
    return session
