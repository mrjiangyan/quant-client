
from data.model.t_symbol import Symbol
from sqlalchemy import func
from typing import List, Optional
from sqlalchemy.orm import Session

# 根据类型以及unicode去查询记录
def get_by_symbol(db_sess:Session, symbol: str, market:str)-> Optional[Symbol]:
    return db_sess.query(Symbol).filter_by(symbol=symbol, market= market).first()

def getAll(db_sess:Session) -> List[Symbol]:
    return db_sess.query(Symbol).all()
