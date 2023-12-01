from __future__ import (absolute_import, division, print_function, unicode_literals)
from .BaseStrategy import BaseStrategy

import backtrader as bt

class KeltnerChannelStrategy(BaseStrategy):
    params = (
        ("atr_period", 14),
        ("mult", 1.5),
    )

    def __init__(self):
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)
        self.middle_band = bt.indicators.ExponentialMovingAverage(self.data.close, period=20)
        self.upper_band = self.middle_band + self.atr * self.params.mult
        self.lower_band = self.middle_band - self.atr * self.params.mult

    def next(self):
        buy_signal = self.data.close > self.upper_band
        sell_signal = self.data.close < self.lower_band
        if buy_signal:
            self.internal_buy()
            
        elif sell_signal:
            self.internal_sell()
