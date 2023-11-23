
from data.model.t_symbol import Symbol
from sqlalchemy import func
from typing import Optional
from data.enum.model_type_enum import SourceTypeEnum

from sqlalchemy import Column, DateTime, func, Integer, String

# 根据类型以及unicode去查询记录
def get_by_symbol(db_sess, symbol: str)-> Optional[Symbol]:
    return db_sess.query(Symbol).filter_by(symbol=symbol).first()


