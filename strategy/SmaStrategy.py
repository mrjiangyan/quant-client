from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from .BaseStrategy import BaseStrategy


class SmaStrategy(BaseStrategy):
    params = (
        ("name", '5天线穿越10天线的策略'), 
        ("min_volume", 10*10000), # 最小要求的成交量
        ("max_kdj_j", 40), #最大kdj值
        ("max_macd_macd", 0), 
        ("min_price", 1.8), 
        ("volume_threshold", 2),  # 调整到 1.5 效果很差
        ("average_volume_period", 50),  # Period for calculating average volume
        ("price_change_threshold", 0.25),  # 6日最大跌幅超过这个幅度，还是有很大缓跌的可能性
        ("day_price_change_threshold", 0.1),  # 最大日震荡幅度或者跌幅
        ("sell_gain_percentage", [0.3, 0.2, 0.15]),  # 涨幅达到20%时卖出
    )

    def __init__(self):
        super().__init__()  # 调用父类的构造函数
        self.volume = self.data.volume
        self.average_volume = bt.indicators.SimpleMovingAverage(self.volume, period=self.params.average_volume_period)
       
               
    def next(self): 
        if not self.check_allow_sell_or_buy():
                return
        if self.position:
                sell_signal = False
                distince_days = (self.data.datetime.date(0) - self.buy_date_data['date']).days
                if not sell_signal:
                    sell_signal = distince_days > 14
                    if  sell_signal:
                        self.log(f'锁仓2周时间限制条件满足')
                if not sell_signal and distince_days<=7:
                    sell_signal = self.calculate_profit_percentage() > self.params.sell_gain_percentage[0]
                    if  sell_signal:
                        self.log(f'卖出涨幅1周内{self.params.sell_gain_percentage[0]*100:.2f}%条件满足')
                
                if not sell_signal and distince_days<=10:
                    sell_signal = self.calculate_profit_percentage() > self.params.sell_gain_percentage[1] 
                    if sell_signal:
                        self.log(f'卖出涨幅10天内{self.params.sell_gain_percentage[1]*100:.2f}%条件满足')
                if not sell_signal and 10 < distince_days<=12:
                    sell_signal =  0 < self.calculate_profit_percentage() < 0.03
                    if sell_signal:
                            self.log(f'卖出涨幅12天内涨幅不足3%')
                if not sell_signal and distince_days<=14:
                    sell_signal = self.calculate_profit_percentage() > self.params.sell_gain_percentage[2]
                    if  sell_signal:
                        self.log(f'卖出涨幅2周内{self.params.sell_gain_percentage[2]*100:.2f}%条件满足')
                if sell_signal == False:
                    sell_signal = distince_days > 3 and (self.order.executed.price - self.data.low[0])/ self.order.executed.price  > 0.08
                    if  sell_signal:
                        self.log(f'止损位条件满足')
                
            
                if sell_signal:
                    self.internal_sell()
                    self.reset()
                    return
        #最低策略要求当日最低成交量暂定不能低于10W
        
      
        if not self.position and (
            self.SMA_5[0] > self.SMA_10[0]  # and self.SMA_5[-1] <= self.SMA_10[-1]     
            and self.SMA_10[0] > self.SMA_30[0]   
            and self.data.high[0] < self.bollinger.lines.top[0]
            and (self.J[0] <= self.K[0] or self.J[0]-self.K[0] < 20)
            # and self.rsi[0] < 60
            # and self.J[0] < 80
            and self.data.close[0] > self.params.min_price
            and self.volume[0] > self.average_volume[0] > self.params.min_volume
            # and ( self.SMA_30[0] <= self.SMA_5[0]  or  (self.SMA_30[0]-self.SMA_5[0])/self.SMA_5[0] < 0.05  ) 
        ):
            if self.internal_buy():
                # Log a message or take any action when abnormal volume is detected
                self.print_kdj()
                self.print_macd()
                self.print_rsi()
                self.print_sma()
                self.print_bolling()
             
            
               

