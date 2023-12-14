from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from .BaseStrategy import BaseStrategy

class ContinuousDeclineOpportunityStrategy(BaseStrategy):
    params = (
        ("short_period", 10),
        ("long_period", 50),
        ("macd_short", 12),
        ("macd_long", 26),
        ("macd_signal", 9), 
    )

    def __init__(self):
        super().__init__()  # 调用父类的构造函数
        self.name = '连续阴线快速下跌买入策略'
        # 添加用于判断连续下跌的变量
        self.consecutive_decline_days = 0
        self.data_close = self.data.close
        self.data_volume = self.data.volume

    def consecutive_decline_condition(self):
        # 添加连续下跌的判断条件，可以根据需要进行修改
        # 示例条件：收盘价连续下跌，并且跌幅超过20%
        if (
            self.data_close < self.data_close[-1] and
            self.data_close.pct_change() < -0.20 and
            self.data_volume < self.data_volume[-1] / 2
        ):
            return True
        else:
            return False

    def next(self):
        # sell_signal = self.short_ma < self.long_ma or self.macd.macd[0] < self.macd.signal[0]
        
        # 获取当前交易日的索引
        current_day = len(self.data)

        # 判断连续下跌的条件
        if current_day > 7 and self.consecutive_decline_condition():
            self.consecutive_decline_days += 1
        else:
            self.consecutive_decline_days = 0

        # 在第7天并且满足条件时买入
        buy_signal = self.consecutive_decline_days == 7
       
       
        if buy_signal:
            self.internal_buy()
        elif self.position and sell_signal:
            self.internal_sell()
