from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from .BaseStrategy import BaseStrategy
from loguru import logger


class MACDStrategy(BaseStrategy):
    params = (
        ("macd_level", -0.5),
        ("period", 9),
        ("k_period", 3),
        ("d_period", 3),
        ('overbought_threshold', 80),
        ('oversold_threshold', 40),
    )

    def __init__(self):
        super().__init__()  # 调用父类的构造函数
        self.name = '底部MACD金叉与kdj底部策略'
         # Add your MACD indicator here
        self.macd = bt.indicators.MACD()

        # Add Bollinger Bands
        self.bollinger = bt.indicators.BollingerBands()
        
        self.high_nine = bt.indicators.Highest(self.data.high, period=self.params.period)
        # 9个交易日内最低价
        self.low_nine = bt.indicators.Lowest(self.data.low, period=self.params.period)
        # 计算rsv值
        self.rsv = 100 * bt.DivByZero(
            self.data_close - self.low_nine, self.high_nine - self.low_nine, zero=None
        )
        # 计算rsv的3周期加权平均值，即K值
        self.K = bt.indicators.EMA(self.rsv, period=self.params.k_period, plot=False)
        # D值=K值的3周期加权平均值
        self.D = bt.indicators.EMA(self.K, period=self.params.d_period, plot=False)
        # J=3*K-2*D
        self.J = 3 * self.K - 2 * self.D
       
       
        self.close_prices = self.data.close.get(size=15)  # 获取最近15天的收盘价
        
        self.price_change_15d  = None
        if len(self.close_prices) >= 2:
            self.price_change_15d = (self.close_prices[-1] - self.close_prices[0]) / self.close_prices[0] * 100
           
        
    def next(self): 
        
        # MACD出现日线的金叉，但是
        buy_signal = (self.macd.macd[0] > self.macd.signal[0] and 
                      self.macd.macd[-1] <= self.macd.signal[-1] and
                      self.macd.macd[0] < self.params.macd_level and self.macd.signal[0] < self.params.macd_level and
                       self.J[0] < self.params.oversold_threshold
                      )
        
        # if buy_signal and self.price_change_15d != None:
        #     buy_signal =  self.price_change_15d > -10 
        
        sell_signal = (self.macd.macd[0] < self.macd.signal[0] and 
                       self.macd.macd[-1] >= self.macd.signal[-1]  )
        
        if sell_signal == False:
            sell_signal = self.K[0] < self.params.overbought_threshold and self.K[-1] >= self.params.overbought_threshold
        
        if buy_signal:
            if self.internal_buy() == True:
                self.log(f'K:{self.K[0]:.3f},D:{self.D[0]:.3f},J:{self.J[0]:.3f}')
                # self.log(f'k:{self.kdj.lines.percK[0]:.3f},d:{self.kdj.lines.percD[0]:.3f},j:{self.kdj.lines.percDSlow[0]:.3f}')
                self.log(f'{self.macd.macd[0]}, {self.macd.signal[0]}')
                
        elif sell_signal:
            if self.internal_sell() == True:
                self.log(f'K:{self.K[0]:.3f},D:{self.D[0]:.3f},J:{self.J[0]:.3f}')
                # self.log(f'k:{self.kdj.lines.percK[0]:.3f},d:{self.kdj.lines.percD[0]:.3f},j:{self.kdj.lines.percDSlow[0]:.3f}')
                self.log(f'{self.macd.macd[0]}, {self.macd.signal[0]}')
