from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from .BaseStrategy import BaseStrategy

class MacdCrossStrategy(BaseStrategy):
    params = (
        ("waiting_period", 10),  # 等待期限
        ("period", 9),
        ("k_period", 3),
        ("d_period", 3),
        ('overbought_threshold', 80),
        ('oversold_threshold', 50),
        ("buy_wait_days", 5),  # 等待的天数
    )

    def __init__(self):
        super().__init__()  # 调用父类的构造函数
        self.name = '底部金叉死叉策略'
        # 初始化MACD指标
        self.macd = bt.indicators.MACD(self.data.close)

        self.high_nine = bt.indicators.Highest(self.data.high, period=self.params.period)
        # 9个交易日内最低价
        self.low_nine = bt.indicators.Lowest(self.data.low, period=self.params.period)
        # 计算rsv值
        self.rsv = 100 * bt.DivByZero(
            self.data_close - self.low_nine, self.high_nine - self.low_nine, zero=None
        )
        # 计算rsv的3周期加权平均值，即K值
        self.K = bt.indicators.EMA(self.rsv, period=self.params.k_period, plot=False)
        # D值=K值的3周期加权平均值
        self.D = bt.indicators.EMA(self.K, period=self.params.d_period, plot=False)
        # J=3*K-2*D
        self.J = 3 * self.K - 2 * self.D
       
        # 追踪最近的金叉和死叉
        self.cross_countdown = 0
        self.gold_crocss_dif =0 
        self.gold_crocss_dea =0 
        self.gold_crocss_date = None
        self.buy_trigger_date = None  # 记录触发条件的日期

    def next(self):
        
        current_diff = self.macd.macd[0]
        current_dea = self.macd.signal[0]
         # 如果MACD线上穿信号线，重置等待期限
        if current_diff >= current_dea and current_diff< 0 and self.macd.macd[-1] < self.macd.signal[-1] and self.J[0] < self.params.oversold_threshold:
            self.cross_countdown = self.params.waiting_period
            self.gold_crocss_dif = current_diff
            self.gold_crocss_dea = current_dea
            self.gold_crocss_date = self.data.datetime.date(0)
            self.buy_trigger_date = None
            
            
            #and self.J[0] < self.params.oversold_threshold

        # 如果等待期限大于零，执行买入
        if self.cross_countdown > 0 and current_diff <= current_dea and current_diff < 0 and self.macd.macd[-1] > self.macd.signal[-1]:
            self.buy_trigger_date = self.data.datetime.date(0)

        if self.buy_trigger_date and (self.data.datetime.date(0) - self.buy_trigger_date).days >= self.params.buy_wait_days:
            if self.internal_buy():
                self.cross_countdown = 0
                self.log(f"金叉: 日期:{self.gold_crocss_date.isoformat()} DIF: {self.gold_crocss_dif}, DEA: {self.gold_crocss_dea}")
                self.log(f"死叉: DIF: {current_diff}, DEA: {current_dea}")
                self.buy_trigger_date = None  # 重置触发条件的日期
      
        # 更新等待期限
        if self.cross_countdown > 0:
            self.cross_countdown -= 1
                
       
            
       
