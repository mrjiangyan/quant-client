from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from .BaseStrategy import BaseStrategy


class MacdStrategy(BaseStrategy):
    params = (
        ("name", '底部MACD金叉与kdj底部策略'), 
        ("macd_level", -0.5),
        ("period", 9),
        ("k_period", 3),
        ("d_period", 3),
        ('overbought_threshold', 80),
        ('oversold_threshold', 40),
    )

    def __init__(self):
        super().__init__()  # 调用父类的构造函数
       
       
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
                       and self.data.volume[0] > 10 * 10000
                      )
        
        # if buy_signal and self.price_change_15d != None:
        #     buy_signal =  self.price_change_15d > -10 
        
         
        if buy_signal and self.internal_buy():
                self.log(f'K:{self.K[0]:.3f},D:{self.D[0]:.3f},J:{self.J[0]:.3f}')
                self.log(f'{self.macd.macd[0]}, {self.macd.signal[0]}')
                
        elif self.position:
            sell_signal = (self.macd.macd[0] < self.macd.signal[0] and 
                       self.macd.macd[-1] >= self.macd.signal[-1]  )
        
            if sell_signal == False:
                sell_signal = self.K[0] < self.params.overbought_threshold and self.K[-1] >= self.params.overbought_threshold
     
            if sell_signal and self.internal_sell():
                self.log(f'K:{self.K[0]:.3f},D:{self.D[0]:.3f},J:{self.J[0]:.3f}')
                # self.log(f'k:{self.kdj.lines.percK[0]:.3f},d:{self.kdj.lines.percD[0]:.3f},j:{self.kdj.lines.percDSlow[0]:.3f}')
                self.log(f'{self.macd.macd[0]}, {self.macd.signal[0]}')
