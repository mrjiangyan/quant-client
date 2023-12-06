
from .BaseStrategy import BaseStrategy
import backtrader as bt

#macd趋势分析
class MacdTrendStrategy(BaseStrategy):
    params = (
        ("macd_short", 12),
        ("macd_long", 26),
        ("macd_signal", 9),
        ("macd_level", -0.5),
        ('oversold_threshold', 20),
        ("period", 9),
        ("k_period", 3),
        ("d_period", 3),
        ('overbought_threshold', 80),
    )

    def __init__(self):
        # Define the MACD indicator
        self.macd = bt.indicators.MACD()
        
        self.high_nine = bt.indicators.Highest(self.data.high, period= self.params.period)
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

    def next(self):
        # Access MACD, signal, and histo values
        current_diff = self.macd.macd[0]
        current_dea = self.macd.signal[0]
       
    
        # Check if dif is rising for three consecutive days and other conditions
        if (current_diff > self.macd.macd[-2] and current_diff < self.params.macd_level and 
                current_diff <  current_dea
                and  self.J[0] < self.params.oversold_threshold
                ):
            # MACD line crossed above the signal line (Golden Cross) - Generate buy signal
            if self.internal_buy() == True:
                self.log(f'K:{self.K[0]:.3f},D:{self.D[0]:.3f},J:{self.J[0]:.3f}')
                self.log(f"DIF: {current_diff}, DEA: {current_dea}")
  

