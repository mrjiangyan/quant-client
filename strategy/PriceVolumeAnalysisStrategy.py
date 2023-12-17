from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from .BaseStrategy import BaseStrategy
import datetime

class PriceVolumeAnalysisStrategy(BaseStrategy):
    params = (
        ("lookback_days", 60),
        ("price_drop_threshold", 0.3),
        ("volume_increase_threshold", 1.0),
        ("future_lookback_days", 20),
        ("min_volume_threshold", 100000),  # 设置成交量的最小阈值为10w
        ("max_daily_drop_percentage", 0.10),  # 买入日的价格跌幅不能超过10%
        ("max_consecutive_drop_days", 12),  # 最大连续下跌天数
        ("min_avg_volume_10days", 10000),  # 前10天的平均成交量阈值
    )

    def __init__(self):
        super().__init__()  # 调用父类的构造函数
        self.name = '价格成交量底部趋势回测分析'
        self.data_close = self.data.close
        self.data_volume = self.data.volume
        self.avg_price = bt.indicators.SimpleMovingAverage(self.data_close, period=self.params.lookback_days)
        self.avg_volume_10days = bt.indicators.SimpleMovingAverage(self.data_volume, period=10)

    def next(self):
        if len(self.avg_price) == 0:
            return
        if len(self.data_volume) <5:
            return
        # if len(self.avg_volume_5days) == 0 or self.avg_volume_5days[0] == 0:
        #         return
        sell_signal = self.params.sell_cross and (self.macd.macd[0] < self.macd.signal[0] and 
                       self.macd.macd[-1] >= self.macd.signal[-1]  )
        if sell_signal == False:
            sell_signal = self.calculate_profit_percentage() > self.params.sell_gain_percentage
          
        price_drop_percentage = (self.data_close[0] - self.avg_price[0]) / self.avg_price[0]
      
        
        volume_5days = [self.data_volume.get(ago=-i, size=1)[0] for i in range(1, min(5, len(self.data_volume)))]
             
             
        avg_volume_5days = sum(volume_5days) / len(volume_5days) if volume_5days else 0


        if avg_volume_5days ==0:
            return
        
        # 计算过去10天的下跌天数 
        consecutive_drop_days = 0
        for i in range(1, 20):
            if self.data_close[-i] < self.data_close[-i - 1]:
                consecutive_drop_days += 1

       
        volume_increase_percentage = (self.data_volume[0] - avg_volume_5days) / avg_volume_5days
       
        if (
            self.check_allow_sell_or_buy() 
            and price_drop_percentage < -self.params.price_drop_threshold 
            and volume_increase_percentage > self.params.volume_increase_threshold
            and self.macd.macd[0] < 0 and self.macd.macd[0] < self.macd.signal[0]
            and self.data_volume[0] > self.params.min_volume_threshold
            and (self.data_close[0] - self.data_close[-1]) / self.avg_price[-1] > -self.params.max_daily_drop_percentage  # 新增条件：当日价格跌幅不超过10%
            and consecutive_drop_days < self.params.max_consecutive_drop_days
            and self.avg_volume_10days[0] > self.params.min_avg_volume_10days
           
          ):
            if self.internal_buy():
                self.print_kdj()
                self.print_macd()
                self.log(f"满足条件：价格下跌{price_drop_percentage*100:.2f}%, 成交量增加{volume_increase_percentage*100:.2f}%")
              
        elif self.position and sell_signal:
            self.internal_sell()      


