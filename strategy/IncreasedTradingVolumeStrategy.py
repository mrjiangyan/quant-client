from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from .BaseStrategy import BaseStrategy


class IncreasedTradingVolumeStrategy(BaseStrategy):
    params = (
        ("volume_threshold", 2),  # Volume threshold (adjust as needed)
        ("average_volume_period", 50),  # Period for calculating average volume
        # ("price_change_threshold", 0.15),  # Price change threshold (20%)
        ("sell_gain_percentage", 0.20),  # 涨幅达到20%时卖出
    )

    def __init__(self):
        super().__init__()  # 调用父类的构造函数
        self.name = '当日成交量异常放大监控'
        self.volume = self.data.volume
        self.average_volume = bt.indicators.SimpleMovingAverage(self.volume, period=self.params.average_volume_period)
        self.previous_close = self.datas[0].close(-1)  # Close price of the previous day

        
    def next(self): 
         #最低策略要求当日最低成交量暂定不能低于10W
          if not self.position and (
            # self.macd.macd[0] < self.macd.signal[0]
            # and self.macd.macd[0] < 0
            # and 
            self.check_allow_sell_or_buy()
            and self.volume[0] > self.params.volume_threshold * self.average_volume[0] > 20 * 10000
            # and abs((self.data.close[0] - self.previous_close[0]) / self.previous_close[0]) <= self.params.price_change_threshold
          ) and self.internal_buy():
            # Log a message or take any action when abnormal volume is detected
            self.log(f'当日成交量: {self.volume[0]}, {self.params.average_volume_period}天平均成交量: {self.average_volume[0]}')
            self.log(f"昨日收盘价:{self.previous_close[0]}, 开盘价: {self.datas[0].open[0]:.2f}, 最高价: {self.datas[0].high[0]:.2f}, 最低价: {self.datas[0].low[0]:.2f}, 收盘价: {self.datas[0].close[0]:.2f}, 交易量: {self.volume[0]:.2f}")
            self.log(f'监测日-MACD: DIF:{self.macd.macd[0]}, DEA:{self.macd.signal[0]}, MACD:{self.macd.macd - self.macd.signal}')
            self.print_kdj()
            self.print_macd()
            self.print_rsi()
          
          sell_signal = self.params.sell_cross and (self.macd.macd[0] < self.macd.signal[0] and 
                       self.macd.macd[-1] >= self.macd.signal[-1]  and self.rsi[0] > self.params.rsi_overbought )
          if sell_signal == False:
            sell_signal = self.calculate_profit_percentage() > self.params.sell_gain_percentage
          if self.position and sell_signal:
              self.internal_sell()
     

               

