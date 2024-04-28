from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from .BaseStrategy import BaseStrategy
import datetime
from loguru import logger

class FastDropReboundStrategy(BaseStrategy):
    params = (
        ("name", '快速下跌反弹策略'), 
        ("lookback_days", 8),  # Lookback period for checking highest price
        ("min_down_days", 5),  # 最近7个交易日中至少有5天的最低价要低于上一个交易日的最低价
        ("recent_days", 4),  # 最近4个交易日的最低价均需要低于上一个交易日
    )

    def __init__(self, *argv):
        # used to modify parameters
        super().__init__(argv[0])
        self.filtered_dates = []
        self.consecutive_down_days = 0  # 用于追踪连续阴线的数量
        
    def has_dropped_more_than_25_percent(self):
            # 获取过去 10 天的最高价和最低价
        high_prices = [self.data.high.get(ago=-i, size=1)[0] for i in range(0, 10)]
        
        # 计算最近 10 天的最高价
        highest_high = max(high_prices)
        
        # 计算当前价格距离最近 10 天的最高价的百分比
        current_price = self.data.close[0]
        percent_drop = ((highest_high - current_price) / highest_high) * 100
        
        # 如果下跌超过 25%，返回 True，否则返回 False
        return percent_drop > 25
   
    def has_consecutive_down_days(self):
        self.consecutive_down_days = 0
        recent_lows = [self.data.low.get(ago=-i, size=1)[0] for i in range(1, 7 + 1)]
        
        # 检查最近7个交易日中至少有5天的最低价要低于上一个交易日的最低价
        min_days_below_prev = sum(1 for low, prev_low in zip(recent_lows, recent_lows[1:]) if low < prev_low)
        
        # print(recent_lows)
        # logger.info(min_days_below_prev)
        if min_days_below_prev >= self.params.min_down_days:
            # 检查最近4个交易日的最低价均需要低于上一个交易日
            if all(low < prev_low for low, prev_low in zip(recent_lows[-self.params.recent_days:], recent_lows[-self.params.recent_days-1:-1])):
                return True
        return False
    
    def next(self):
        # and self.has_dropped_more_than_25_percent()
        # 在满足条件时执行买入和卖出
        if self.has_consecutive_down_days() :
            # 确保第二天的交易日可用
            if len(self.datas[0]) > 1:
                # 在第二天进行买入
                self.internal_buy();
                    
        elif self.position:
            # 买入的第二天进行卖出
            if len(self.datas[0]) > 1:
                self.internal_sell()
