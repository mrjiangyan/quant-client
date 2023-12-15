from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from ..BaseStrategy import BaseStrategy

class ContinuousDeclineOpportunityMonitorStrategy(BaseStrategy):
    params = (
        ("decline_percentage", 0.2),  # 下跌比例
        ("consecutive_decline_days_config", 4),  # 连续下跌天数
        ("volume_shrink_percentage", 0.25),  # 量能萎缩百分比
        ("day_decline_percentage", 0.4),  # 单日跌幅超过40%
        ("print_signal_condition", False),  # 打印输出信号条件不满足的情况
    )

    def __init__(self):
        super().__init__()  # 调用父类的构造函数
        self.name = '连续阴线快速下跌监控策略'
        # 添加用于判断连续下跌的变量
        self.consecutive_decline_days = 0
        self.data_close = self.data.close
        self.data_open = self.data.open
        self.data_volume = self.data.volume
        self.first_day_close = 0  # 记录第一天下跌的收盘价
        self.first_day_volume = 0  # 记录第一天下跌的收盘价

    def consecutive_decline_condition(self):
        # 添加连续下跌的判断条件，比较下跌百分比与第一天下跌的收盘价
        # 示例条件：收盘价连续下跌，并且跌幅超过20%
        if (
            (self.first_day_close - self.data_close) / self.first_day_close > self.params.decline_percentage and
            self.data_volume / self.first_day_volume < self.params.volume_shrink_percentage
        ):
            return True
        else:
            return False
        
    def is_decline(self):
        # 添加连续下跌的判断条件，比较下跌百分比与第一天下跌的收盘价
        # 示例条件：收盘价连续下跌，并且跌幅超过20%
        if (
            self.data_close < self.data_close[-1] and
            self.data_close <= self.data_open
        ):
            # 如果是第一天下跌，记录第一天的收盘价
            return True
        else:
            return False

    def check_volume(self):
        max_volume = min_volume = 0
        for i in range(-self.consecutive_decline_days, 0):
            volume = self.data.volume[i]
            # print(self.data.datetime.date(0),self.data.datetime.date(i),volume)
            if volume > max_volume:
                max_volume = volume
            elif min_volume == 0 or volume < min_volume:
                min_volume = volume

        # print(self.data.datetime.date(0), max_volume, min_volume)
        return max_volume > 100000 and min_volume > 10000
    
    
    def check_macd(self):
        return self.macd.macd[0] < 0.1 and self.macd.macd[0] < self.macd.signal[0]
    
    def check_day_decline_percentage(self):
        for i in range(-self.consecutive_decline_days, 0):
            close = self.data.close[i]
            # print(self.data.datetime.date(0),self.data.datetime.date(i),volume)
            if (self.data.close[i-1] - close)/self.data.close[i-1] > self.params.day_decline_percentage:
                print(self.data.datetime.date(0), self.data.close[i-1], close, (self.data.close[i-1] - close)/self.data.close[i-1])
                return False
        return True
    
    def next(self):
        if not self.check_allow_sell_or_buy():
            return
         # 判断连续下跌的条件
        if self.is_decline():
            self.consecutive_decline_days += 1
            if self.consecutive_decline_days == 1:
                self.first_day_close = self.data_close[0]
                self.first_day_volume = self.data_volume[0]
        else:
            self.consecutive_decline_days = 0
            self.first_day_close = 0
            self.first_day_volume = 0
            return
      
        buy_signal = False
        
        if buy_signal == False:
            buy_signal = self.consecutive_decline_condition() 
           
        if buy_signal == False:
            buy_signal = self.check_macd()
              
        if buy_signal == False:
            buy_signal = self.check_volume()
                

        if buy_signal and (self.consecutive_decline_days >= self.params.consecutive_decline_days_config
            and self.check_day_decline_percentage() 
            and  (self.first_day_close - self.data_close) / self.first_day_close > self.params.decline_percentage) :
            self.log(f'{self.data.datetime.date(0)}连续下跌天数:{self.consecutive_decline_days}')
            if self.first_day_close !=0:
                self.log(f'连续下跌百分比:{(self.first_day_close - self.data_close) / self.first_day_close}')
            self.log(f'监测日-MACD: DIF:{self.macd.macd[0]}, DEA:{self.macd.signal[0]}, MACD:{self.macd.macd - self.macd.signal}')
            # 打印每日开盘、收盘、最高、最低价格以及成交量
            log_content = ''
            
            for i in range(-self.consecutive_decline_days, 1):
                    print(i)
                    log_content += f"Date: {self.data.datetime.date(i)} | "
                    log_content += f"开盘: {self.data.open[i]:.2f} | "
                    log_content += f"最高: {self.data.high[i]:.2f} | "
                    log_content += f"最低: {self.data.low[i]:.2f} | "
                    log_content += f"收盘: {self.data.close[i]:.2f} | "
                    log_content += f"成交量: {self.data.volume[i]}\n"
            self.log(log_content)   
                
        
