#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec
from loguru import logger
from contextlib import contextmanager

def global_init(db_file):
    global __factory
    global __db_file

    if __factory:
        return


    if not db_file or not db_file.strip():
        raise Exception("db_file is not found")

    __db_file = db_file
    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    logger.info(f"Connection String {conn_str}")

    engine = sa.create_engine(conn_str, 
                              echo=True, 
                              pool_size=5, # 数据库连接池初始化的容量
                      max_overflow=10, # 连接池最大溢出容量，该容量+初始容量=最大容量。超出会堵塞等待，等待时间为timeout参数值默认30
                      pool_recycle=7200, # 重连周期
                      )
    __factory = orm.sessionmaker(bind=engine)

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

def create_readonly_ssession() -> Session:

    conn_str = f'sqlite:///{__db_file.strip()}?check_same_thread=False'
    engine = sa.create_engine(conn_str, echo=True)
    # 创建会话工厂
    Session = orm.sessionmaker(bind=engine)

    # 创建只读会话
    session = Session(readonly=True)
    # session = scoped_session(Session)
    return session



SqlAlchemyBase = dec.declarative_base()

__factory = None