from __future__ import (absolute_import, division, print_function, unicode_literals)

from .BaseStrategy import BaseStrategy


class RapidReboundContinuousDeclineStrategy(BaseStrategy):
    params = (
        ("name", '连续阴线快速下跌买入策略'), 
        ("decline_percentage", 0.6),  # 下跌幅度
        ("consecutive_decline_days_config", 4),  # 连续下跌天数
        ("volume_shrink_percentage", 0.80),  # 量能萎缩百分比
    )

    def __init__(self, *argv):
            # used to modify parameters
        super().__init__(argv[0])
        # 添加用于判断连续下跌的变量
        self.consecutive_decline_days = 0
        self.data_close = self.data.close
        self.data_open = self.data.open
        self.data_volume = self.data.volume
        self.first_day_close = 0  # 记录第一天下跌的收盘价
        self.first_day_volume = 0  # 记录第一天下跌的收盘价
        self.first_day = None

    # 计算下跌幅度以及成交量
    def consecutive_decline_condition(self):
        decline_ratio = (self.first_day_close - self.data_close) / self.first_day_close
        #如果是最高位的下跌，需要下跌50%以上
        if self.is_highest_close_30(self.consecutive_decline_days):
            return decline_ratio > 0.6
        # 添加连续下跌的判断条件，比较下跌百分比与第一天下跌的收盘价
    #    return (self.first_day_close - self.data_close) / self.first_day_close > self.params.decline_percentage
        return decline_ratio >  self.params.decline_percentage
        
    def is_decline(self):
       return self.data_close < self.data_open and (self.data_close[0] - self.data_close[-1])/ self.data_close[-1] < 0.02
       

    def is_highest_close_30(self, index):
        highest_close= 0
        for i in range(-index-30, -index):
            close = self.data.close[i]
            if close > highest_close:
                highest_close = close
        # Check if today's and the previous two days' closing prices are the highest within the last 30 days
        return (
            self.data.close[-index] == highest_close or
            self.data.close[-index-1] == highest_close or
            self.data.close[-index-2] == highest_close
        )

    def check_volume(self, days):
        max_volume = 0
        total_volumes = 0
        for i in range(-days+1, 0):
            volume = self.data.volume[i]
            total_volumes+=volume
            if volume > max_volume:
                max_volume = volume

        avarige_volume = total_volumes/days 
        #需要满足最大成交量，最小成交量以及购买日的成交量需要小于平均成交量的需求
        return max_volume > 200000 and (avarige_volume > self.data.volume[0] and avarige_volume > 100000) or self.data.volume[0] < 10000
    

    def reset(self):
        self.consecutive_decline_days = 0
        
    def next(self):
        if not self.check_allow_sell_or_buy():
            return   
        if self.position:
            sell_signal = False
            distince_days = (self.data.datetime.date(0) - self.buy_date_data['date']).days
            if sell_signal == False:
                sell_signal = distince_days > 14
                if  sell_signal:
                    self.log(f'锁仓2周时间限制条件满足')
            
        
            if sell_signal:
                self.internal_sell()
                self.reset()
                return
         # 判断连续下跌的条件
        if self.is_decline():
            self.consecutive_decline_days += 1
            if self.consecutive_decline_days == 1:
                self.first_day_close = self.data_close[0]
                self.first_day_volume = self.data_volume[0]
                self.first_day = self.data.datetime.date(0)
        else :
            self.consecutive_decline_days = 0
      

        buy_signal = self.consecutive_decline_days >= self.params.consecutive_decline_days_config and self.consecutive_decline_condition()
        
        if buy_signal and self.last_sell_day and (self.data.datetime.date(0) - self.last_sell_day).days < 10:
            buy_signal =  False
       
        if buy_signal:
           buy_signal = self.check_volume(self.consecutive_decline_days)
           if not buy_signal:
                self.log('成交量条件不满足')
                days = self.consecutive_decline_days 
                # self.reset()
                self.print_detail(days)
                return
           else:
                self.log(f'成交量均线:5D:{self.volume_sma5[0]:.0f},10D:{self.volume_sma10[0]:.0f},30D:{self.volume_sma30[0]:.0f}')
            
        if buy_signal and not self.position and self.internal_buy():
                days = self.consecutive_decline_days 
                self.reset()
                self.print_detail(days)
               
    def print_detail(self, days):
        self.log(f'总股本{self.params.symbol.shares_outstanding}')
        self.log(f'连续下跌天数:{days}')
        self.log(f'连续跌幅百分比:{(self.first_day_close - self.data_close) / self.first_day_close}')
        self.print_kdj()
        self.print_macd()
        self.print_bolling()
        # 打印每日开盘、收盘、最高、最低价格以及成交量
        log_content = ''
        
        for i in range(-days, 1):
            log_content += f"Date: {self.data.datetime.date(i)} | "
            log_content += f"开盘: {self.data.open[i]:.2f} | "
            log_content += f"最高: {self.data.high[i]:.2f} | "
            log_content += f"最低: {self.data.low[i]:.2f} | "
            log_content += f"收盘: {self.data.close[i]:.2f} | "
            log_content += f"成交量: {self.data.volume[i]}\n"
        self.log(log_content)         
        
