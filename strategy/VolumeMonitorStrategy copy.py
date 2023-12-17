from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from .BaseStrategy import BaseStrategy


class VolumeMonitorStrategy(BaseStrategy):
    params = (
        ("volume_threshold", 2),  # Volume threshold (adjust as needed)
        ("average_volume_period", 5),  # Period for calculating average volume
        ("price_change_threshold", 0.2),  # Price change threshold (20%)
   
    )

    def __init__(self):
        super().__init__()  # 调用父类的构造函数
        self.name = '成交量异常监控'
        self.volume = self.data.volume
        self.average_volume = bt.indicators.SimpleMovingAverage(self.volume, period=self.params.average_volume_period)
        self.previous_close = self.datas[0].close(-1)  # Close price of the previous day

        
    def next(self): 
         #最低策略要求当日最低成交量暂定不能低于10W
          if (
            self.volume[0] > 10 * 10000
            and self.check_allow_sell_or_buy()
            and self.volume[0] > self.params.volume_threshold * self.average_volume[0]
            and self.J[0] < 30
            and self.macd.macd[0] < -0.2
            and abs((self.data.close[0] - self.previous_close[0]) / self.previous_close[0]) <= self.params.price_change_threshold
          ):
            # Log a message or take any action when abnormal volume is detected
            self.log(f'当日成交量: {self.volume[0]}, {self.params.average_volume_period}天平均成交量: {self.average_volume[0]}')
            self.log(f"昨日收盘价:{self.previous_close[0]}, 开盘价: {self.datas[0].open[0]:.2f}, 最高价: {self.datas[0].high[0]:.2f}, 最低价: {self.datas[0].low[0]:.2f}, 收盘价: {self.datas[0].close[0]:.2f}, 交易量: {self.volume[0]:.2f}")
              
            self.log(f'监测日-MACD: DIF:{self.macd.macd[0]}, DEA:{self.macd.signal[0]}, MACD:{self.macd.macd - self.macd.signal}')
            self.print_kdj()

               

