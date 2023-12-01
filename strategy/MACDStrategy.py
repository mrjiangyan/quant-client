from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from .BaseStrategy import BaseStrategy

class MACDStrategy(BaseStrategy):
    params = (
        ("short_period", 12),
        ("long_period", 26),
        ("signal_period", 9),
        ("macd_level", -0.5),
    )

    def __init__(self):
         # Add your MACD indicator here
        self.macd = bt.indicators.MACD()

        # Add Bollinger Bands
        self.bollinger = bt.indicators.BollingerBands()

    def next(self):
        
        current_price = self.data.close[0]
        macd_value = self.macd.lines.macd[0]
        signal_value = self.macd.lines.signal[0]
        # 新增条件
        avg_5d_volume = self.data.volume.rolling(window=5).mean()
        avg_10d_volume = self.data.volume.rolling(window=10).mean()
        price_change_15d = self.data.close.pct_change(30).sum()


        print('price_change_15d', price_change_15d)
        print('avg_5d_volume',avg_5d_volume[-1])
        print('avg_10d_volume', avg_10d_volume[-1])
        
        buy_signal = (self.macd.macd[0] > self.macd.signal[0] and 
                      self.macd.macd[-1] <= self.macd.signal[-1] and
                      avg_5d_volume[-1] < avg_10d_volume[-1] and
                      price_change_15d < -0.1)
        
        sell_signal = (self.macd.macd[0] < self.macd.signal[0] and 
                       self.macd.macd[-1] >= self.macd.signal[-1])
        
        if buy_signal:
            self.internal_buy()
            
        elif sell_signal:
            self.internal_sell()
