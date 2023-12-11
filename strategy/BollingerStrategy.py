from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from .BaseStrategy import BaseStrategy
import datetime

class BollingerStrategy(BaseStrategy):
    params = (
        ("bollinger_period", 20),  # Bollinger Bands period
        ("bollinger_dev", 2),  # Bollinger Bands standard deviation
        ("sell_profit_threshold", 0.1),  # Profit threshold for selling within 5 days
        ("max_hold_days", 5),  # Maximum number of days to hold a position
    
    )

    def __init__(self):
        super().__init__()  # 调用父类的构造函数
        self.name = '布林线下轨击穿策略'
        # Create Bollinger Bands indicator
        self.bollinger = bt.indicators.BollingerBands(self.data.close, period= self.params.bollinger_period, devfactor= self.params.bollinger_dev)
        # self.bollinger = bt.indicators.BollingerBands()
        # 记录符合条件的日期
        self.filtered_dates = []

    def calculate_profit_percentage(self):
        if self.position:
            buy_price = self.position.price
            current_price = self.data.close[0]
            return (current_price - buy_price) / buy_price
        return 0.0
    
    def next(self):
        close_price = self.datas[0].close[0]
        low_price = self.datas[0].low[0]
        # 在满足条件时执行买入和卖出
        if not self.position and low_price < self.bollinger.lines.bot[0] * 0.9:
            if self.internal_buy():
                buy_date = self.data.datetime.date(0)
                max_sell_date = buy_date + datetime.timedelta(days=self.params.max_hold_days)
                self.filtered_dates.append((buy_date, max_sell_date))
                self.log("Bollinger Bands: Upper: {:.2f}, Middle: {:.2f}, Lower: {:.2f}".format(
                self.bollinger.lines.top[0],
                self.bollinger.lines.mid[0],
                self.bollinger.lines.bot[0]
                ))
        elif self.position:
            if len(self.filtered_dates) > 0:
                buy_date, max_sell_date = self.filtered_dates[-1]
                if self.data.datetime.date(0) >= max_sell_date or self.calculate_profit_percentage() >= self.params.sell_profit_threshold:
                    self.internal_sell()
               