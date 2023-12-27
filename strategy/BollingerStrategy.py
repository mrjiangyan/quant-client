from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from .BaseStrategy import BaseStrategy
import datetime
from loguru import logger

class BollingerStrategy(BaseStrategy):
    params = (
        ("name", '布林线短期内从触碰上轨到击穿下轨策略'), 
        ("lookback_days", 8),  # Lookback period for checking highest price
        ("max_hold_days", 60),
        ("min_consecutive_down_days", 3),  # 至少要有3天连续阴线
        ("cup_depth_percentage", 10),  # 杯部深度百分比
        ("handle_depth_percentage", 5),  # 柄部深度百分比
    )

    def __init__(self):
        super().__init__()  # 调用父类的构造函数
        self.filtered_dates = []
        self.consecutive_down_days = 0  # 用于追踪连续阴线的数量
        
        self.cup_handle_indicator = bt.indicators.CupHandle(depth_pct_cup=self.params.cup_depth_percentage,
                                                            depth_pct_handle=self.params.handle_depth_percentage)


    def has_highest_price_touched_upper_band(self, lookback_days):
        # 获取过去 lookback_days 的最高价
        high_prices = [self.data.high.get(ago=-i, size=1)[0] for i in range(0, lookback_days)]

        upper_bands = [self.bollinger.lines.top.get(ago=-i, size=1)[0] for i in range(0, lookback_days)]

        # 判断是否有任意一天的最高价触及布林线上轨
        for i, (high, upper_band) in enumerate(zip(high_prices, upper_bands)):
            if high > upper_band:
                #logger.info(f'{high}, {upper_band}')
                return i
        return None
      
   
    
    def has_consecutive_down_days(self):
        self.consecutive_down_days = 0
        for i in range(-self.params.lookback_days, 0):
         
            if (self.data.close[i] < self.data.open[i] and self.data.close[i] < self.data.close[i - 1] 
                and self.data.high[i] > self.bollinger.lines.bot[i] and self.data.close[i] > self.bollinger.lines.bot[i]
                ):
                self.consecutive_down_days += 1
        else:
            if self.consecutive_down_days >= self.params.min_consecutive_down_days:
                return True
            self.consecutive_down_days = 0

        return self.consecutive_down_days >= self.params.min_consecutive_down_days
    
    #计算macd逻辑，需要macd的dif和dea都小于0并且都小于0以及 dif需要小于dea
    def check_buy_macd(self):
        return self.macd.macd[0] <-0.12 and self.macd.signal[0] <-0.12 and self.macd.macd[0] <= self.macd.signal[0]
    
    def check_buy_kdj(self):
        return self.J[0] < 20
    
    #检查购买日的最低价格是否低于布林线下轨
    def check_low_price(self):
        return self.datas[0].low[0] < self.bollinger.lines.bot[0] or self.datas[0].low[0] < self.bollinger.lines.bot[0] * 1.01
   
    #检查购买日的收盘价格是否高于布林线下轨
    def check_buy_day_close_price(self):
        return self.datas[0].close[0] > self.bollinger.lines.bot[0]
    
    def calculate_percent_drop(self, close_yesterday, close_today):
        """
            计算两天收盘价下跌百分比

            参数：
            close_yesterday (float): 前一天的收盘价
            close_today (float): 当天的收盘价

            返回：
            float: 下跌百分比，如果上涨或持平则返回 None
        """
        return ((close_yesterday - close_today) / close_yesterday) * 100

    def check_max_drop(self, close_prices):
        # logger.info(close_prices)
        """
        检查当前天到过去的-index天之间的价格序列中是否存在跌幅超过15%的日期。

        参数：
        index (int): 负数，表示过去的天数
        close_prices (list or numpy array): 价格序列，包含至少 `index` 个元素

        返回：
        bool: 如果存在跌幅超过15%的日期，返回True；否则返回False。
        """
        for i in range(0,len(close_prices)-1):
            # print(i, close_prices[i-1], close_prices[i])
            percent_drop = ((close_prices[i+1]-close_prices[i]) / close_prices[i+1]) * 100
            # logger.info(percent_drop)
            if percent_drop > 15:
                return False
        return True
         
    def next(self):
        low_price = self.datas[0].low[0]
        current_date = self.data.datetime.date(0)

        # 在满足条件时执行买入和卖出
        if self.check_low_price() and self.check_buy_macd() and self.check_buy_kdj():
            index = self.has_highest_price_touched_upper_band(self.params.lookback_days)
            if index != None:
                # print(self.data.datetime.datetime(0), self.data.close[0], index,  self.data.datetime.datetime(-index-1),self.data.close[-index-1] )
                day_index = -index-1
                # 
                #print(self.data.close[day_index] , self.data.close[0] , self.calculate_percent_drop(self.data.close[day_index], self.data.close[0]))
            # 如果index <=2 表示 跳跃太厉害，这样的股票没有快速下跌的上涨机会
            if index and index <=5 and ( self.calculate_percent_drop(self.data.close[day_index], self.data.close[0]) > 12 and 
            self.has_consecutive_down_days() and 
            
            self.check_buy_day_close_price() and
            self.check_max_drop([self.data.close.get(ago=-i, size=1)[0] for i in range(0, index)]) 
            ) and self.internal_buy():
                self.log(f"有 {self.consecutive_down_days} 天连续阴线满足要求！")
                self.log(f'间隔天数:{index}')
                date = self.data.datetime.datetime(day_index)
                open_price = self.data.open[day_index]
                high_price = self.data.high[day_index]
                low_price = self.data.low[day_index]
                close_price = self.data.close[day_index]
                volume = self.data.volume[day_index]
                max_sell_date = current_date + datetime.timedelta(days=self.params.max_hold_days)
                self.filtered_dates.append((current_date, max_sell_date))
                self.log(f'买入-MACD: DIF:{self.macd.macd[0]}, DEA:{self.macd.signal[0]}, MACD:{self.macd.macd - self.macd.signal}')
                self.log("买入-布林线: 上轨: {:.2f}, 中轨: {:.2f}, 下轨: {:.2f}".format(
                        self.bollinger.lines.top[0],
                        self.bollinger.lines.mid[0],
                        self.bollinger.lines.bot[0]
                    ))
                self.log(f"买入-KDJ: K:{self.K[0]:.3f},D:{self.D[0]:.3f},J:{self.J[0]:.3f}")
                self.log(f"触碰布林线上轨:{date.strftime('%Y-%m-%d')}: 上轨:{self.bollinger.lines.top[day_index]:.2f},中轨:{self.bollinger.lines.mid[day_index]:.2f}, 下轨: {self.bollinger.lines.bot[day_index]:.2f}")
                self.log('触碰上轨日期: %s, 开盘价: %.2f, 最高价: %.2f, 最低价: %.2f, 收盘价: %.2f, 交易量: %.2f' %
                    (date.strftime('%Y-%m-%d'), open_price, high_price, low_price, close_price, volume))
                
        elif self.position:
            if len(self.filtered_dates) > 0:
                buy_date, max_sell_date = self.filtered_dates[-1]
                sell_signal = (self.macd.macd[0] < self.macd.signal[0] and 
                       self.macd.macd[-1] >= self.macd.signal[-1]  )
                if (
                    sell_signal or
                    current_date >= max_sell_date or
                    ((current_date - buy_date).days <= 50 and self.calculate_profit_percentage() >= 0.5) or
                    ((current_date - buy_date).days < 100 and self.calculate_profit_percentage() >= 1.0) or 
                    ((current_date - buy_date).days == 25 and self.calculate_profit_percentage() <= 0.1) or 
                    self.calculate_profit_percentage() < -0.08
                ):
                    if self.internal_sell():
                        self.log(f'买入卖出间隔天数:{ (current_date - buy_date).days}')
