from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
from .BaseStrategy import BaseStrategy
from loguru import logger
import pandas as pd

class MacdCrossStrategy(BaseStrategy):
    params = (
        ("short_window", 12),
        ("long_window", 26),
        ("signal_window", 9),
        ("waiting_period", 10),  # 等待期限
        ("period", 9),
        ("k_period", 3),
        ("d_period", 3),
        ('overbought_threshold', 80),
        ('oversold_threshold', 20),
    )

    def __init__(self):
        # 初始化MACD指标
        self.macd = bt.indicators.MACD()

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

    def next(self):
        
        current_diff = self.macd.macd[0]
        current_dea = self.macd.signal[0]
         # 如果MACD线上穿信号线，重置等待期限
        if current_diff >= current_dea and current_diff< 0 and self.macd.macd[-1] < self.macd.signal[-1] and self.J[0] < self.params.oversold_threshold:
            self.cross_countdown = self.params.waiting_period
            self.gold_crocss_dif = current_diff
            self.gold_crocss_dea = current_dea
            self.gold_crocss_date = self.data.datetime.date(0)
            

        # 如果等待期限大于零，执行买入
        elif self.cross_countdown > 0 and current_diff <= current_dea  and current_diff< 0 and self.macd.macd[-1] > self.macd.signal[-1] and self.J[0] < self.params.oversold_threshold:
            if self.internal_buy():
                self.cross_countdown = 0
                self.log(f"金叉: 日期:{self.gold_crocss_date.isoformat()} DIF: {self.gold_crocss_dif}, DEA: {self.gold_crocss_dea}")
                self.log(f"死叉: DIF: {current_diff}, DEA: {current_dea}")

        # 更新等待期限
        if self.cross_countdown > 0:
            self.cross_countdown -= 1
                
       
            
       
