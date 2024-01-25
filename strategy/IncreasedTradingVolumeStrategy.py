from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from .BaseStrategy import BaseStrategy


class IncreasedTradingVolumeStrategy(BaseStrategy):
    params = (
        ("name", '当日成交量异常放大监控'), 
        ("min_volume", 10*10000), # 最小要求的成交量
        ("max_kdj_j", 50), #最大kdj值
        ("max_macd_macd", 0), 
        ("min_price", 2), 
        ("volume_threshold", 2),  # 调整到 1.5 效果很差
        ("average_volume_period", 50),  # Period for calculating average volume
        ("price_change_threshold", 0.25),  # 6日最大跌幅超过这个幅度，还是有很大缓跌的可能性
        ("day_price_change_threshold", 0.1),  # 最大日震荡幅度或者跌幅
        ("sell_gain_percentage", [0.3, 0.2, 0.15]),  # 涨幅达到20%时卖出
    )

    def __init__(self, *argv):
        # used to modify parameters
        super().__init__(argv[0])
        self.volume = self.data.volume
        self.average_volume = bt.indicators.SimpleMovingAverage(self.volume, period=self.params.average_volume_period)
        self.consecutive_decline_days = 0
        
    def check_volume(self, days):
       
        # Check volume condition for the last 5 days
        for i in range(-days + 1, 0):
            volume = self.data.volume[i]
            if volume > self.data.volume[0]:
                return False

        # Check other volume conditions
        return True
        
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
        
        # 判断连续下跌的条件
        if self.is_decline():
            self.consecutive_decline_days += 1
        else :
            self.consecutive_decline_days = 0
            
        if not self.position and (
            self.volume[0] > self.params.volume_threshold * self.average_volume[0] > self.params.min_volume
            #J需要小于60
            and self.J[0] < self.params.max_kdj_j
            #macd需要为负值
            # and self.check_volume(5)
            # and self.rsi[0] < 30
            and self.macd.macd[0] < self.params.max_macd_macd
            and self.data.high[0] < self.bollinger.lines.top[0]
            and self.data.low[0] > self.bollinger.lines.bot[0] * 1.01
            and (self.params.symbol.shares_outstanding == 0 or 0.005 < self.volume[0]/self.params.symbol.shares_outstanding < 0.05)
            #最低价格限制
            and self.data.close[0] > self.params.min_price
            # and self.data.high[0] > self.SMA_5[0]
            and (
                # (self.data.close[-50] - self.data.close[0]) / self.data.close[-50] < self.params.price_change_threshold * 2
                # and
                # (self.data.close[-30] - self.data.close[0]) / self.data.close[-30] < self.params.price_change_threshold * 1.5
                # and
                (self.data.close[-5] - self.data.close[0]) / self.data.close[-5] < self.params.price_change_threshold 
                and
                (self.data.close[-1] - self.data.close[0]) / self.data.close[-1] < self.params.day_price_change_threshold
                and
                (self.data.high[0] - self.data.low[0]) / self.data.low[0] < self.params.day_price_change_threshold
                )
        ):
            print(self.consecutive_decline_days)
            # 判断连续下跌天数
            if self.consecutive_decline_days > 3:
                self.log('发出信号,等待布林线触发下轨了以后买入')
                return
            if self.internal_buy():
                # Log a message or take any action when abnormal volume is detected
                self.log(f'当日成交量: {self.volume[0]}, {self.params.average_volume_period}天平均成交量: {self.average_volume[0]},5日均量:{self.volume_sma5[0]:.2f},10日均量:{self.volume_sma10[0]:.2f}')
                self.log(f"昨日收盘价:{self.data.close[-1]:.2f}, 开盘价: {self.datas[0].open[0]:.2f}, 最高价: {self.datas[0].high[0]:.2f}, 最低价: {self.datas[0].low[0]:.2f}, 收盘价: {self.datas[0].close[0]:.2f}, 交易量: {self.volume[0]:.2f}")
                self.print_kdj()
                self.print_macd()
                self.print_rsi()
                self.print_sma()
                self.print_bolling()
                self.print_turnover_rate(self.volume[0])
            
      # sell_signal = self.params.sell_cross and (self.macd.macd[0] < self.macd.signal[0] and 
      #               self.macd.macd[-1] >= self.macd.signal[-1]  and self.rsi[0] > self.params.rsi_overbought )
      # if sell_signal == False:
      #   sell_signal = self.calculate_profit_percentage() > self.params.sell_gain_percentage
      # if self.position and sell_signal:
      #     self.internal_sell()
     

               

