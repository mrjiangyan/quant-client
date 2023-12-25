from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from .BaseStrategy import BaseStrategy
import datetime

class ContinuousDeclineOpportunityStrategy(BaseStrategy):
    params = (
        ("decline_percentage", 0.28),  # 下跌幅度
        ("consecutive_decline_days_config", 6),  # 连续下跌天数
        # ("volume_shrink_percentage", 0.33),  # 量能萎缩百分比
        ("sell_cross", True),  # 是否根据死叉卖出
        ("sell_gain_percentage", 0.20),  # 涨幅达到20%时卖出
        ("day_decline_percentage", 0.4),  # 单日跌幅限制
        ("print_signal_condition", True),  # 打印输出信号条件不满足的情况
    )

    def __init__(self):
        super().__init__()  # 调用父类的构造函数
        self.name = '连续阴线快速下跌买入策略'
        # 添加用于判断连续下跌的变量
        self.consecutive_decline_days = 0
        self.data_close = self.data.close
        self.data_open = self.data.open
        self.data_volume = self.data.volume
        self.first_day_close = 0  # 记录第一天下跌的收盘价
        self.first_day_volume = 0  # 记录第一天下跌的收盘价

    # 计算下跌幅度以及成交量
    def consecutive_decline_condition(self):
            # 添加连续下跌的判断条件，比较下跌百分比与第一天下跌的收盘价
        # 示例条件：收盘价连续下跌，并且跌幅超过20%
        if (
            (self.first_day_close - self.data_close) / self.first_day_close > self.params.decline_percentage
            # and self.first_day_volume != 0 and self.data_volume / self.first_day_volume < self.params.volume_shrink_percentage
        ):
            return True
        else:
            return False
        
    def is_decline(self):
       return (
            (self.data_open[0] - self.data_close[0]) / self.data_open[0] > 0.05
            or
            (self.data_close[-1] - self.data_close[0]) / self.data_close[-1] > 0.05
        ) and  self.data_close < self.data_open

    def check_volume(self):
        max_volume = 0
        total_volumes = 0
        for i in range(-self.consecutive_decline_days, 0):
            volume = self.data.volume[i]
            total_volumes+=volume
            if volume > max_volume:
                max_volume = volume

        #需要满足最大成交量，最小成交量以及购买日的成交量需要小于平均成交量的需求
        return max_volume > 100000 and total_volumes/self.consecutive_decline_days > self.data.volume[0]
    
    
    def check_macd(self):
        return self.macd.macd[0] < 0.1 and self.macd.macd[0] < self.macd.signal[0]
    
    def check_day_decline_percentage(self):
        for i in range(-self.consecutive_decline_days, 0):
            close = self.data.close[i]
            if (self.data.close[i-1] - close)/self.data.close[i-1] > self.params.day_decline_percentage:
                return False
        return True
    
    
    def next(self):
        sell_signal = self.params.sell_cross and (self.macd.macd[0] < self.macd.signal[0] and 
                       self.macd.macd[-1] >= self.macd.signal[-1]  )
        if sell_signal == False:
            sell_signal = self.calculate_profit_percentage() > self.params.sell_gain_percentage
       
        # if sell_signal == False and self.buy_date_data:
        #     sell_signal = (self.data.datetime.datetime(0) - self.buy_date_data['date']).days >=10
         # 判断连续下跌的条件
        if self.is_decline():
            self.consecutive_decline_days += 1
            if self.consecutive_decline_days == 1:
                self.first_day_close = self.data_close[0]
                self.first_day_volume = self.data_volume[0]
        else:
            self.consecutive_decline_days = 0
      

        buy_signal = True
        
        if buy_signal == True:
            buy_signal = self.consecutive_decline_days >= self.params.consecutive_decline_days_config and self.consecutive_decline_condition()
            if self.params.print_signal_condition and not buy_signal and self.consecutive_decline_days == self.params.consecutive_decline_days_config - 1 :
                    self.log(f'{self.data.datetime.date(0)},天数:{self.consecutive_decline_days}')
           
        if buy_signal == True:
            buy_signal = self.check_macd()
            if self.params.print_signal_condition and not buy_signal:
                self.log(f'{self.data.datetime.date(0)},macd条件不满足,DIF:{self.macd.macd[0]}, DEA:{self.macd.signal[0]}, MACD:{self.macd.macd - self.macd.signal}')
            
        if buy_signal == True:
            buy_signal = self.check_volume()
            if self.params.print_signal_condition and not buy_signal:
                self.log(f'{self.data.datetime.date(0)},成交量条件不满足')

        if buy_signal == True:
            buy_signal = self.check_day_decline_percentage()
            if self.params.print_signal_condition and not buy_signal:
                self.log(f'{self.data.datetime.date(0)},下跌幅度条件不满足')
                
        if buy_signal and not self.position and  self.internal_buy():
                self.log(f'连续下跌天数:{self.consecutive_decline_days}')
                self.log(f'连续百分比:{(self.first_day_close - self.data_close) / self.first_day_close}')
                self.print_kdj()
                self.print_macd()
                # 打印每日开盘、收盘、最高、最低价格以及成交量
                log_content = ''
                for i in range(-self.consecutive_decline_days, 1):
                    log_content += f"Date: {self.data.datetime.date(i)} | "
                    log_content += f"开盘: {self.data.open[i]:.2f} | "
                    log_content += f"最高: {self.data.high[i]:.2f} | "
                    log_content += f"最低: {self.data.low[i]:.2f} | "
                    log_content += f"收盘: {self.data.close[i]:.2f} | "
                    log_content += f"成交量: {self.data.volume[i]}\n"
                self.log(log_content)   
                
        elif self.position and sell_signal:
            self.internal_sell()
