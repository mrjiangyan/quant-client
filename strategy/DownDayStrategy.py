from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from .BaseStrategy import BaseStrategy


class DownDayStrategy(BaseStrategy):
    params = (
         ("drop_threshold", 0.25),  # 下跌最低阈值设置%
    )

    def __init__(self):
        super().__init__()  # 调用父类的构造函数
        self.name = '大幅下跌并收阳线的监控策略'
      
        
    def next(self): 
        sell_signal = self.params.sell_cross and (self.macd.macd[0] < self.macd.signal[0] and 
                       self.macd.macd[-1] >= self.macd.signal[-1]  )
        if sell_signal == False:
            sell_signal = self.calculate_profit_percentage() > self.params.sell_gain_percentage
      
        #最低策略要求当日最低成交量暂定不能低于10W
        if self.data.close[0] > self.data.open[0] and (self.data.close[-1] - self.data.close[0]) / self.data.close[-1] > self.params.drop_threshold:
                # 当日下跌超过30%并且是收阳线
            if self.internal_buy():
                self.print_kdj()
                self.print_macd()
                self.log(f"符合条件:下跌超过{self.params.drop_threshold*100:.2f}%，当日为阳线 - Date: {self.data.datetime.date(0)} | Open: {self.data.open[0]:.2f} | Close: {self.data.close[0]:.2f}")
        elif self.position and sell_signal:
                self.internal_sell()      


               

