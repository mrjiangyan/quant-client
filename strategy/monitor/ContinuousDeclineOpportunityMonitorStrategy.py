from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from ..ContinuousDeclineOpportunityStrategy import ContinuousDeclineOpportunityStrategy

class ContinuousDeclineOpportunityMonitorStrategy(ContinuousDeclineOpportunityStrategy):
    params = (
        ("decline_percentage", 0.2),  # 下跌比例
        ("consecutive_decline_days_config", 5),  # 连续下跌天数
        ("day_decline_percentage", 0.4),  # 单日跌幅超过40%
    )

    def __init__(self):
        super().__init__()  # 调用父类的构造函数
        self.name = '连续阴线快速下跌监控策略'
       

    def next(self):
       
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
           
        # if buy_signal == False:
        #     buy_signal = self.check_macd()
              
        # if buy_signal == False:
        #     buy_signal = self.check_volume()
                

        if buy_signal   and  (self.consecutive_decline_days >= self.params.consecutive_decline_days_config
            and self.check_day_decline_percentage() 
           ) and self.check_allow_sell_or_buy() :
            self.log(f'{self.data.datetime.date(0)}连续下跌天数:{self.consecutive_decline_days}')
            if self.first_day_close !=0:
                self.log(f'连续下跌百分比:{(self.first_day_close - self.data_close) / self.first_day_close}')
            self.log(f'监测日-MACD: DIF:{self.macd.macd[0]}, DEA:{self.macd.signal[0]}, MACD:{self.macd.macd - self.macd.signal}')
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
                
        
