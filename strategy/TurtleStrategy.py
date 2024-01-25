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

class TurtleStrategy(BaseStrategy):
    params = (
        ("name", '海龟交易策略'), 
        ('long_period',20),
        ('short_period',10),  
    )

    def __init__(self, *argv):
        # used to modify parameters
        super().__init__(argv[0])
        self.buyprice = 0      
        self.buycomm = 0      
        self.buy_size = 0      
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

   
    def next(self): 
        if not self.check_allow_sell_or_buy():
                return
        if self.order:
            return        
        #入场：价格突破上轨线且空仓时        
        if self.buy_signal > 0 and self.buy_count == 0:                                 
            self.buy_size = self.broker.getvalue() * 0.01 / self.ATR            
            self.buy_size  = int(self.buy_size  / 100) * 100                             
            self.sizer.p.stake = self.buy_size             
            buy_signal =  self.data.close[0] < self.bollinger.lines.top[0] and self.data.volume[0] > 8 * 10000 \
                    and round(self.SMA_5[0],2) > round(self.SMA_10[0],2) > round(self.SMA_15[0],2) \
                    and 0.01 < (self.SMA_5[0]-self.SMA_30[0])/self.SMA_30[0] < 0.2 \
                    and self.data.low[0] < self.SMA_30[0] < self.SMA_60[0] \
                    and self.turnover_rate(self.data.volume[0]) < 25
                
            if buy_signal and self.internal_buy():     
                print(self.data.volume[0], self.turnover_rate(self.data.volume[0]))   
                self.buy_count += 1    
                self.print_kdj()
                self.print_bolling()
                self.print_macd()
                self.print_sma()
                self.print_rsi()
                self.print_turnover_rate(self.data.volume[0])          
        #加仓：价格上涨了买入价的0.5的ATR且加仓次数少于3次（含）        
        elif self.data.close > self.buyprice+0.5*self.ATR[0] and self.buy_count > 0 and self.buy_count <=4:   
                    
            self.buy_size  = self.broker.getvalue() * 0.01 / self.ATR            
            self.buy_size  = int(self.buy_size  / 100) * 100            
            self.sizer.p.stake = self.buy_size      
            buy_signal =  self.data.close[0] < self.bollinger.lines.top[0] and self.data.volume[0] > 8 * 10000 \
                    and round(self.SMA_5[0],2) > round(self.SMA_10[0],2) > round(self.SMA_15[0],2) \
                    and 0.01 < (self.SMA_5[0]-self.SMA_30[0])/self.SMA_30[0] < 0.2 \
                    and self.data.low[0] < self.SMA_30[0] < self.SMA_60[0] \
                    and self.turnover_rate(self.data.volume[0]) < 25
            if buy_signal and self.internal_buy():    
                logger.info(f'{self.data.volume[0]}, {self.turnover_rate(self.data.volume[0])}')  
                self.buy_count += 1    
                self.print_kdj()
                self.print_bolling()
                self.print_macd()
                self.print_sma()
                self.print_rsi()
                self.print_turnover_rate(self.data.volume[0])    
        #离场：价格跌破下轨线且持仓时        
        elif self.sell_signal < 0 and self.buy_count > 0:            
            if self.internal_sell():        
                self.print_kdj()
                self.print_bolling()
                self.print_macd()
                self.print_sma()
                self.print_rsi()
                self.print_turnover_rate(self.data.volume[0])             
                self.buy_count = 0        
        #止损：价格跌破买入价的2个ATR且持仓时        
        elif self.data.close < (self.buyprice - 2*self.ATR[0]) and self.buy_count > 0:           
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

