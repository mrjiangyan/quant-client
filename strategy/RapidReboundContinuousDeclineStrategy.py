from __future__ import (absolute_import, division, print_function, unicode_literals)

from .BaseStrategy import BaseStrategy


class RapidReboundContinuousDeclineStrategy(BaseStrategy):
    params = (
        ("decline_percentage", 0.28),  # 下跌幅度
        ("consecutive_decline_days_config", 6),  # 连续下跌天数
        # ("volume_shrink_percentage", 0.33),  # 量能萎缩百分比
        ("sell_cross", True),  # 是否根据死叉卖出
        ("sell_gain_percentage", [0.2, 0.4]),  # 涨幅达到20%时卖出
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
        self.wait_for_volume_contraction = False
        self.wait_for_bolling_contraction = False
        self.first_day = None

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

    def check_volume(self, days):
        max_volume = 0
        total_volumes = 0
        for i in range(-days, 0):
            volume = self.data.volume[i]
            total_volumes+=volume
            if volume > max_volume:
                max_volume = volume

        #需要满足最大成交量，最小成交量以及购买日的成交量需要小于平均成交量的需求
        return max_volume > 100000 and total_volumes/days > self.data.volume[0], total_volumes/days
    
    def check_min_volume(self, days):
        min_volume = self.data.volume[0]
        for i in range(-days, 0):
            volume = self.data.volume[i]
            if volume < min_volume:
                min_volume = volume

        #需要满足最大成交量，最小成交量以及购买日的成交量需要小于平均成交量的需求
        return min_volume == self.data.volume[0]
    
    def check_bolling(self):
        #保证买入那一天的最低价要在布林线下轨上方
        return self.data.low[0] > self.bollinger.lines.bot[0]
    
    
    def check_macd(self):
        return self.macd.macd[0] < 0.1 and self.macd.macd[0] < self.macd.signal[0]
    
    def check_day_decline_percentage(self):
        for i in range(-self.consecutive_decline_days, 0):
            close = self.data.close[i]
            if (self.data.close[i-1] - close)/self.data.close[i-1] > self.params.day_decline_percentage:
                return False
        return True
    
    
    def next(self):
            
         # 判断连续下跌的条件
        if self.is_decline():
            self.consecutive_decline_days += 1
            if self.consecutive_decline_days == 1:
                self.first_day_close = self.data_close[0]
                self.first_day_volume = self.data_volume[0]
        else:
            self.consecutive_decline_days = 0
      

        buy_signal = True
        
        if self.wait_for_volume_contraction:
            #量能萎缩的条件下需要具有最高的优先级，计算从下跌第一天以来的成交量均值
            days = (self.data.datetime.date(0)- self.first_day).days
            buy_signal, average_volume = self.check_volume(days)
            self.log(f"{self.data.datetime.date(0)},成交量条件{  '' if buy_signal else '不' }满足, 平均成交量{average_volume},当日成交量:{self.data.volume[0]}")
            buy_signal = buy_signal and average_volume* 0.8 > self.data_volume[0] or self.check_min_volume(days)
            # 需要买入日期的成交量不能大于50万
            buy_signal = buy_signal
            # buy_signal = self.check_min_volume(days)
            
        elif self.wait_for_bolling_contraction:
            buy_signal = self.check_bolling()
            if self.params.print_signal_condition and not buy_signal:
                self.log(f"{self.data.datetime.date(0)},布林线下轨条件{  '' if buy_signal else '不' }满足, 下轨:{self.bollinger.lines.bot[0]},最低价:{self.data.low[0]}")
                # 这个条件必须要强制作为最后一个条件来判断，其具有最高的优先级
        else:
            if buy_signal == True:
                buy_signal = self.consecutive_decline_days >= self.params.consecutive_decline_days_config and self.consecutive_decline_condition()
                if self.params.print_signal_condition and not buy_signal and self.consecutive_decline_days == self.params.consecutive_decline_days_config - 1 :
                        self.log(f'{self.data.datetime.date(0)},天数:{self.consecutive_decline_days}')
            
            if buy_signal == True:
                buy_signal = self.check_macd()
                if self.params.print_signal_condition and not buy_signal:
                    self.log(f'{self.data.datetime.date(0)},macd条件不满足,DIF:{self.macd.macd[0]}, DEA:{self.macd.signal[0]}, MACD:{self.macd.macd - self.macd.signal}')
                        
           
            if buy_signal == True:
                buy_signal = self.check_day_decline_percentage()
                if self.params.print_signal_condition and not buy_signal:
                    self.log(f'{self.data.datetime.date(0)},下跌幅度条件不满足')
            
            if buy_signal == True:
                buy_signal = self.check_bolling()
                if self.params.print_signal_condition and not buy_signal:
                    self.log(f'{self.data.datetime.date(0)},布林线下轨条件不满足, 下轨:{self.bollinger.lines.bot[0]},最低价:{self.data.low[0]}')
                     # 这个条件必须要强制作为最后一个条件来判断，其具有最高的优先级
                    self.wait_for_bolling_contraction = True
         
            if buy_signal == True:
                buy_signal, average_volume = self.check_volume(self.consecutive_decline_days)
                if self.params.print_signal_condition and not buy_signal:
                    self.log(f'买入成交量条件不满足, 平均成交量:{average_volume},当日成交量:{self.data_volume[0]}')
                    # 这个条件必须要强制作为最后一个条件来判断，其具有最高的优先级
                    self.wait_for_volume_contraction = True
                    self.first_day = self.data.datetime.date(-self.consecutive_decline_days)
                else:
                    self.log(f'{self.data.datetime.date(0)},成交量条件满足, 平均成交量{average_volume}')
            
        if buy_signal == True and self.last_sell_day and (self.data.datetime.date(0) - self.last_sell_day).days < 15:
            buy_signal =  False
        
        buy_signal =  buy_signal == True and self.data_volume[0] < 50 * 10000 and self.data_close[0] > 0.9
            
            
        if buy_signal and not self.position and  self.internal_buy():
                self.log(f'连续下跌天数:{self.consecutive_decline_days}')
                self.log(f'连续百分比:{(self.first_day_close - self.data_close) / self.first_day_close}')
                
                self.wait_for_volume_contraction  = False
                self.wait_for_bolling_contraction = False
                self.print_kdj()
                self.print_macd()
                self.print_bolling()
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
               
                
        elif self.position:
            # # sell_signal = self.params.sell_cross and (self.macd.macd[0] < self.macd.signal[0] and 
            # #            self.macd.macd[-1] >= self.macd.signal[-1]  ) and self.macd.macd[0] > 0
            # if self.params.print_signal_condition and sell_signal:
            #         self.log(f'卖出死叉条件满足')
            sell_signal = False
            if sell_signal == False:
                sell_signal = (self.data.datetime.date(0) - self.buy_date_data['date']).days > 14
                if self.params.print_signal_condition and sell_signal:
                    self.log(f'锁仓2周时间限制条件满足')
            if sell_signal == False and  (self.data.datetime.date(0) - self.buy_date_data['date']).days<=7:
                sell_signal = self.calculate_profit_percentage() > self.params.sell_gain_percentage[0]
                if self.params.print_signal_condition and sell_signal:
                    self.log(f'卖出涨幅1周内{self.params.sell_gain_percentage[0]*100:.2f}%条件满足')
            if sell_signal == False:
                sell_signal = self.calculate_profit_percentage() > self.params.sell_gain_percentage[1]
                if self.params.print_signal_condition and sell_signal:
                    self.log(f'卖出涨幅2周内{self.params.sell_gain_percentage[1]*100:.2f}%条件满足')
            

        
            if sell_signal:
                self.internal_sell()
