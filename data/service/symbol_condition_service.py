
from data.model.t_symbol_condition import SymbolCondition
from sqlalchemy import func
from typing import Optional
from data.enum.model_type_enum import SourceTypeEnum

from sqlalchemy import Column, DateTime, func, Integer, String

# 根据类型以及unicode去查询记录
def get_by_symbol(db_sess, symbol: str, market:str)-> Optional[SymbolCondition]:
    return db_sess.query(SymbolCondition).filter_by(symbol=symbol, market= market).first()


