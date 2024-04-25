from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from .BaseStrategy import BaseStrategy
from loguru import logger
# 交易策略

# 回顾一下海龟交易法则的策略思路：

# 入场条件：当收盘价突破20日价格高点时，买入一单元股票；

# 加仓条件：当价格大于上一次买入价格的0.5个ATR（平均波幅），买入一单元股票，加仓次数不超过3次；

# 止损条件：当价格小于上一次买入价格的2个ATR时清仓；

# 离场条件：当价格跌破10日价格低点时清仓


#TODO: 待增加的逻辑 1.横盘每日振幅在5%以内的并且大于等于5日左右的剔除掉 2.需要增加逻辑，将非美国的股票尤其是非洲和中国的剔除掉  
class TurtleStrategy(BaseStrategy):
    params = (
        ("name", '海龟交易策略'), 
        ('long_period',20),
        ('short_period',10),  
    )

    def __init__(self, *argv):
        # used to modify parameters
        super().__init__(argv[0])
        self.buycomm = 0      
        self.buy_count = 0       
        # 海龟交易法则中的唐奇安通道和平均波幅ATR        
        self.H_line = bt.indicators.Highest(self.data.high(-1), period=self.p.long_period)        
        self.L_line = bt.indicators.Lowest(self.data.low(-1), period=self.p.short_period)       
        self.TR = bt.indicators.Max((self.data.high(0)- self.data.low(0)),\
                                    abs(self.data.close(-1)-self.data.high(0)), \
                                    abs(self.data.close(-1)  - self.data.low(0)))        
        self.ATR = bt.indicators.SimpleMovingAverage(self.TR, period=14)       
        # 价格与上下轨线的交叉      
        self.buy_signal = bt.ind.CrossOver(self.data.close(0), self.H_line)        
        self.sell_signal = bt.ind.CrossOver(self.data.close(0), self.L_line)    

        self.lowest_low = bt.indicators.Lowest(self.data.low, period=10)
        self.highest_high = bt.indicators.Highest(self.data.high, period=10)

    # 判断卖出逻辑, 如果满足下述条件中的任意1个就卖出
    # 1.如果10天内上涨超过50%则卖出
    # 2.如果开盘价和收盘价都超出布林线，则收盘就卖出
    # 3.连续两天收盘价超出布林线，则第二天卖出。
    def is_sell(self):
        distince_days = (self.data.datetime.date(0) - self.buy_date_data['date']).days
        # 1.如果10天内上涨超过50%则卖出
        if distince_days <= 10 and (self.data.high[0]-self.buyprice)/self.buyprice > 0.5:
            self.log('满足10天内涨幅超过50%的收益率卖出')
            return True
        if  distince_days > 4 and self.data.close[0] > self.data.open[0] > self.bollinger.lines.top[0]:
            self.log('满足开盘价和收盘价都超出布林线的上轨的卖出策略')
            return True
        if distince_days > 8 and self.data.close[-1] > self.bollinger.lines.top[-1]*1.02 and  self.data.close[0]> self.bollinger.lines.top[0]:
            self.log('满足连续两天收盘价超出布林线上轨的卖出策略')
            return True
        if (self.data.open[0]- self.bollinger.lines.top[0]) /self.bollinger.lines.top[0]> 0.15:
            self.log('满足高开价格超过布林线上轨15%的卖出策略')
            return True
        if distince_days >=7 and self.find_up_days(7, 7):
            self.log('满足连续7天上涨卖出策略')
            #连续7天上涨考虑卖出
            return True
        # if  self.data.close[-1] > self.data.open[-1] and self.data.open[0] >= self.data.close[-1] and self.data.close[0] <= self.data.open[-1] :
        #     self.log('满足阴线把阳线完全包住的卖出策略')
        #     return True
        if distince_days > 60:
            self.log('满足买入超过60天卖出的卖出策略')
            return True
        return False
    
    # 判断买入逻辑，排除掉一些极端情况
    # 1.排除掉最近10天上涨超过 50% 的情况
    # 2.排除掉最近10天波动没有超过5%的情况
    def filter_buy(self):
        # 暂时排除掉股价大于25元的标的
        if self.data.open[0] > 25:
            return True
        # 前面10天内不能有涨幅超过20%的日期
        if self.find_up_day(10, 0.2):
           self.log('过去10天内有单日涨幅超过20%情况出现, 不予以考虑')
           return True 
       
        days = 25 
        rate = -0.20
        if self.find_down_day(days, rate):
        #    self.log(f'过去{days}天内有单日跌幅幅超过{rate*100:.2f}%情况出现, 不予以考虑')
           return True 
        days = 10 
        minimal_volume = 10000
        #过滤极小成交量情况
        if self.find_minimal_volume(days, minimal_volume):
           return True 
        # 1.排除掉最近10天上涨超过 50% 的情况
        # recent_lowest = self.lowest_low.lines[0]
        # print((self.data.open[0] -recent_lowest) / recent_lowest)
        # if (self.data.open[0] -recent_lowest) / recent_lowest > 0.5:
        #     self.log('不满足10天内涨幅不超过50%的条件')
        #     return True
        # latest_price = self.find_latest_price_with_days(10)
        # if (self.data.high[0] - latest_price)/ latest_price > 0.5:
        #     self.log('不满足10天内涨幅不超过35%的条件')
        #     return True
        
        # # 2.排除掉最近10天波动没有超过5%的情况
        # print((self.highest_high.lines[0] - recent_lowest)/recent_lowest)
        # if  (self.highest_high.lines[0] - recent_lowest)/recent_lowest < 0.05  :
        #     self.log('不满足最近10天波动超过5%的情况')
        #     return True
        
        
        # 这个指标是比较有效的，连续上涨 下跌的概率就很大
        if self.find_up_days(7, 7) and (self.data.close[0] - self.data.close[-7])/ self.data.close[-7] > 0.3:
            #判断涨幅，如果涨幅超过30%的才不能考虑
            #self.log('过去7天内有超过7天上涨, 涨幅过大')
            return True
        if self.find_up_days(12, 10):
                #判断涨幅，如果涨幅超过30%的才不能考虑
            #self.log('过去12天内有超过10天上涨, 涨幅过大')
            return True
        
        # days = 60
        # scale = 0.8
        # latest_price = self.find_latest_price_with_days(days)
        # if (self.data.high[0] - latest_price)/ latest_price > scale:
        #     self.log(f'不满足{days}天内涨幅不超过{scale*100}%的条件')
        #     return True
        
        #寻找过去30天内有超过 昨日成交量10倍的情况出现，不考虑买入 OSPN
        
        #如果买入日期的成交量是之前5天的 5倍以上 则放弃 CDZIP
        return False
    
    # 寻找N天内的最低价
    def find_latest_price_with_days(self, days:int):
        latest_price = self.data.low[0]
        for i in range(-days, 0):
            low = self.data.low[i]
            if low < latest_price:
                latest_price = low
        return latest_price   
    
    def find_up_days(self, days:int, min_days:int):
        up_days = 0
        for i in range(-days, 0):
            if self.data.open[i] < self.data.close[i]:
                up_days = up_days + 1
        return up_days >= min_days     
    
    
    
    def find_up_day(self, days:int, rate:float):
        for i in range(-days, 0):
            if (self.data.close[i] - self.data.close[i-1])/ self.data.close[i-1] > rate:
                return True
        return False
    
    def find_minimal_volume(self, days:int, minimal_volume:int):
        for i in range(-days, 0):
            if self.data.volume[i] < minimal_volume:
                return True
        return False
    
    def find_down_day(self, days:int, rate:float):
        for i in range(-days, 0):
            if (self.data.close[i] - self.data.close[i-1])/ self.data.close[i-1] < rate or (self.data.open[i] - self.data.close[i-1])/ self.data.close[i-1] < rate:
                return True
        return False    
            
    def next(self): 
        if not self.check_allow_sell_or_buy():
                return
        # if self.position:
        #     print('二次买入信号', self.datas[0].datetime.datetime(0), self.buyprice, self.data.close[0], self.ATR[0], self.buyprice + 0.5 * self.ATR[0])    
        #入场：价格突破上轨线且空仓时        
        if self.buy_signal > 0 and not self.position and not self.filter_buy():                                 
            buy_size = self.broker.getvalue() * 0.01 / self.ATR            
            buy_size  = int(buy_size  / 100) * 100                             
            self.sizer.p.stake = buy_size      
            
            # print(1, self.data.close < self.bollinger.lines.top[0] and self.data.volume[0] > 8 * 10000) 
            # print(2, round(self.SMA_5[0],2) > round(self.SMA_10[0],2) > round(self.SMA_15[0],2))     
            # print(3, 0.01 < (self.SMA_5[0]-self.SMA_30[0])/self.SMA_30[0] < 0.2)   
            # print(4, self.data.low[0] < self.SMA_30[0] < self.SMA_60[0] )
            # print(5, self.turnover_rate(self.data.volume[0]) < 25 )
            # print(6, self.datas[0].datetime.datetime(0) )
            buy_signal =  self.data.close < self.bollinger.lines.top[0] and self.data.volume[0] > 8 * 10000 \
                    and round(self.SMA_5[0],2) > round(self.SMA_10[0],2) > round(self.SMA_15[0],2) \
                    and 0.01 < (self.SMA_5[0]-self.SMA_30[0])/self.SMA_30[0] < 0.2 \
                    and self.turnover_rate(self.data.volume[0]) < 25 \
                    and not (self.SMA_5[0] > self.SMA_10[0] > self.SMA_15[0] >  self.SMA_30[0] > self.SMA_60[0]) \
                    # and self.data.low[0] < self.SMA_30[0] < self.SMA_60[0] \
                    
            if buy_signal and self.internal_buy():     
                self.buy_count += 1    
                self.print_kdj()
                self.print_bolling()
                self.print_macd()
                self.print_sma()
                self.print_rsi()
                self.print_turnover_rate(self.data.volume[0])    
                print(self.position)      
        #加仓：价格上涨了买入价的0.5的ATR且加仓次数少于3次（含）        
        elif self.position and self.data.close > self.buyprice + 0.5 * self.ATR[0] and self.buy_count <= 4:   
                    
            buy_size  = self.broker.getvalue() * 0.01 / self.ATR            
            buy_size  = int(buy_size  / 100) * 100            
            self.sizer.p.stake = buy_size      
            buy_signal =  self.data.close[0] < self.bollinger.lines.top[0] and self.data.volume[0] > 8 * 10000 \
                    and round(self.SMA_5[0],2) > round(self.SMA_10[0],2) > round(self.SMA_15[0],2) \
                    and 0.01 < (self.SMA_5[0]-self.SMA_30[0])/self.SMA_30[0] < 0.2 \
                    and not (self.SMA_5[0] > self.SMA_10[0] > self.SMA_15[0] >  self.SMA_30[0] > self.SMA_60[0]) \
                    and self.turnover_rate(self.data.volume[0]) < 25
                    # and self.data.low[0] < self.SMA_30[0] < self.SMA_60[0] \
                  
            if buy_signal and self.internal_buy():    
                self.buy_count += 1    
                self.print_kdj()
                self.print_bolling()
                self.print_macd()
                self.print_sma()
                self.print_rsi()
                self.print_turnover_rate(self.data.volume[0])    
        #离场：价格跌破下轨线且持仓时        
        
        
         #止损：价格跌破买入价的2个ATR且持仓时   
        if self.position and self.is_sell(): #(self.sell_signal < 0 or self.data.close < (self.buyprice - 2 * self.ATR[0])):            
            if self.internal_sell():        
                self.print_kdj()
                self.print_bolling()
                self.print_macd()
                self.print_sma()
                self.print_rsi()
                self.print_turnover_rate(self.data.volume[0])             
                self.buy_count = 0        
            
       

    #记录交易收益情况（可省略，默认不输出结果）
  
    def stop(self):
        if self.trade:
            self.log(f'(组合线:{self.p.long_period},{self.p.short_period})；')

