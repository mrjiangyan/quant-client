from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from .BaseStrategy import BaseStrategy
from loguru import logger
import pandas as pd

class MACDStopLossStrategy(BaseStrategy):
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

         # Add a Simple Moving Average (SMA) for the rolling mean of volume
        self.avg_5d_volume = bt.indicators.SimpleMovingAverage(self.data.volume, period=5)
        
        self.avg_10d_volume = bt.indicators.SimpleMovingAverage(self.data.volume, period=10)

        self.close_prices = self.data.close.get(size=15)  # 获取最近15天的收盘价
       
        
        if len(self.close_prices) >= 2:
            self.price_change_15d = (self.close_prices[-1] - self.close_prices[0]) / self.close_prices[0] * 100
        else:
            self.price_change_15d  = None
            # print(self.close_prices)
            # Handle the case when there are not enough elements in close_prices
            # print("Insufficient data in close_prices.")

    def next(self):
        
        current_price = self.data.close[0]
        macd_value = self.macd.lines.macd[0]
        signal_value = self.macd.lines.signal[0]
        
        # 新增条件
        if self.position and self.broker.getvalue() > 0:
            buy_price = self.position.price
            print(buy_price)
            unrealized_profit_loss = (current_price - buy_price) / buy_price * 100
            if unrealized_profit_loss < -5:
                self.internal_sell()
                self.log(f"Stop-loss triggered. Selling all positions. Unrealized loss: {unrealized_profit_loss:.2f}%")
                return
        # MACD出现日线的金叉，但是
        buy_signal = (self.macd.macd[0] > self.macd.signal[0] and 
                      self.macd.macd[-1] <= self.macd.signal[-1] and
                      self.avg_5d_volume[-1] < self.avg_10d_volume[-1] and
                      self.avg_5d_volume[0] > self.avg_10d_volume[0] 
                      )
        
        if buy_signal and self.price_change_15d != None:
            buy_signal =  self.price_change_15d < -10 
        
        sell_signal = (self.macd.macd[0] < self.macd.signal[0] and 
                       self.macd.macd[-1] >= self.macd.signal[-1] and 
                       self.macd.macd[0] > 0 )
        
        if buy_signal:
            self.internal_buy()
            
        elif sell_signal:
            self.internal_sell()
