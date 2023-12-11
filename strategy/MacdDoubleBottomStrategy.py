from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from .BaseStrategy import BaseStrategy
from datetime import datetime

class MacdDoubleBottomStrategy(BaseStrategy):
    params = (
        ("lookback_period", 50),  # 查找双底的回溯期
        ("macd_level", -0.2),
    )

    def __init__(self):
        super().__init__()  # 调用父类的构造函数
        self.name = 'MACD双重底策略'
         # Add your MACD indicator here
        self.macd = bt.indicators.MACD()

        self.gold_cross1 = None
        self.dead_cross = False
        self.gold_cross12 = False
        self.gold_cross1_date = None
    
    def next(self):
       
       
          # MACD出现日线的金叉，但是
        if self.gold_cross1 != True:
            self.gold_cross1 =  (self.macd.macd[0] > self.macd.signal[0] and 
                        self.macd.macd[-1] <= self.macd.signal[-1] 
                          and
                          self.macd.macd[0] < self.params.macd_level and self.macd.signal[0] < self.params.macd_level 
                        #   and
                        #    self.J[0] < self.params.oversold_threshold
            )
            if self.gold_cross1:
                self.gold_cross1_date  = self.data.datetime.date(0)
                
        if not self.gold_cross1:
            return
        
        if self.dead_cross!= True:
        # print('gold_cross1:', self.data.datetime.date(0).isoformat(), self.macd.macd[0], self.macd.signal[0], self.macd.macd[-1],self.macd.signal[-1])
            self.dead_cross = self.gold_cross1 and (self.macd.macd[0] < self.macd.signal[0] and 
                        self.macd.macd[-1] >= self.macd.signal[-1] 
                         and
                          self.macd.macd[0] < self.params.macd_level and self.macd.signal[0] < self.params.macd_level 
                        #    self.J[0] < self.params.oversold_threshold
            )
      
        if not self.dead_cross:
            return
        
        # print('gold_cross1:',self.gold_cross1)
        # print('dead_cross:',self.dead_cross)
        # print(self.data.datetime.date(0).isoformat(), self.macd.macd[0], self.macd.signal[0], self.macd.macd[-1],self.macd.signal[-1])

        self.gold_cross2 = self.dead_cross and (self.macd.macd[0] > self.macd.signal[0] and 
                      self.macd.macd[-1] <= self.macd.signal[-1] 
                    and
                        self.macd.macd[0] < self.params.macd_level and self.macd.signal[0] < self.params.macd_level 
        )
        # 计算日期差异
        days_difference = (self.data.datetime.date(0) - self.gold_cross1_date).days
        buySignal = self.gold_cross1 and self.dead_cross and self.gold_cross2 and days_difference <= 50
        if buySignal:
            # 在这里执行买入操作，例如 self.buy()
            if self.internal_buy() == True:
                previous = self.datas[-1]
                date = previous.datetime.datetime(-1)
                open_price = previous.open[-1]
                high_price = previous.high[-1]
                low_price = previous.low[-1]
                close_price = previous.close[-1]
                volume = previous.volume[-1]
                self.log(f'{self.macd.macd[0]}, {self.macd.signal[0]}')
                self.log('前一日: %s, 开盘价: %.2f, 最高价: %.2f, 最低价: %.2f, 收盘价: %.2f, 交易量: %.2f' %
                    (date.strftime('%Y-%m-%d %H:%M'), open_price, high_price, low_price, close_price, volume))
                self.gold_cross1 = None
                self.dead_cross = False
                self.gold_cross12 = False