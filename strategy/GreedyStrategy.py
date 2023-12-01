from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from .BaseStrategy import BaseStrategy

class GreedyStrategy(BaseStrategy):
    params = (
        ("short_period", 10),
        ("long_period", 50),
        ("macd_short", 12),
        ("macd_long", 26),
        ("macd_signal", 9), 
    )

    def __init__(self):
        self.short_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.short_period)
        self.long_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.long_period)
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.macd_short,
            period_me2=self.params.macd_long,
            period_signal=self.params.macd_signal,
        )

    def next(self):
        buy_signal = self.short_ma > self.long_ma and self.macd.macd[0] > self.macd.signal[0]
        sell_signal = self.short_ma < self.long_ma or self.macd.macd[0] < self.macd.signal[0]
        if buy_signal:
            self.internal_buy()
            
        elif sell_signal:
            self.internal_sell()
