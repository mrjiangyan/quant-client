from futu import *
import futu as ft
from loguru import logger

quote_ctx = ft.OpenQuoteContext(host='127.0.0.1', port=11111)  # 创建行情对象
snapshot = quote_ctx.get_market_snapshot('HK.00700')

logger.info(snapshot)  # 获取港股 HK.00700 的快照数据
quote_ctx.close() # 关闭对象，防止连接条数用尽


trd_ctx = ft.OpenSecTradeContext(host='127.0.0.1', port=11111)  # 创建交易对象
logger.info(trd_ctx.place_order(price=500.0, qty=100, code="HK.00700", trd_side= ft.TrdSide.BUY, trd_env=ft.TrdEnv.SIMULATE))  # 模拟交易，下单（如果是真实环境交易，在此之前需要先解锁交易密码）

trd_ctx.close()  # 关闭对象，防止连接条数用尽
