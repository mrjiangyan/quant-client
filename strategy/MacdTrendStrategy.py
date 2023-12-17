
from .BaseStrategy import BaseStrategy
import backtrader as bt

#macd趋势分析
class MacdTrendStrategy(BaseStrategy):
    params = (
        ("macd_level", -0.3),
        ('oversold_threshold', 30),
        ("period", 9),
        ("k_period", 3),
        ("d_period", 3),
        ('overbought_threshold', 80),
    )

    def __init__(self):
        super().__init__()  # 调用父类的构造函数
        self.name = '底部MACD金叉趋势预判策略'
        

    def next(self):
        # Access MACD, signal, and histo values
        current_diff = self.macd.macd[0]
        current_dea = self.macd.signal[0]
       
    
        # Check if dif is rising for three consecutive days and other conditions
        if (current_diff > self.macd.macd[-2] and current_diff < self.params.macd_level and 
                current_diff <  current_dea
                and self.J[0] < self.params.oversold_threshold
                ):
            # MACD line crossed above the signal line (Golden Cross) - Generate buy signal
            if self.internal_buy() == True:
                self.log(f'K:{self.K[0]:.3f},D:{self.D[0]:.3f},J:{self.J[0]:.3f}')
                self.log(f"DIF: {current_diff}, DEA: {current_dea}")
  

