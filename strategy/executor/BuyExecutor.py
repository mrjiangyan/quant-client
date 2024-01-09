from __future__ import (absolute_import, division, print_function, unicode_literals)

from ..BaseStrategy import BaseStrategy
from .. import IncreasedTradingVolumeStrategy


class BuyExecutor(BaseStrategy):
    params = (
        ("name", '买入执行器'), 
       
    )

    def __init__(self):
        super().__init__()  # 调用父类的构造函数
    
    def next(self):
        if not self.check_allow_sell_or_buy():
                return
        print(self.params.shared_variable)
            # Access the shared variable to check for buy signals
        if self.params.shared_variable[0] and not self.position:
            # Execute your buy logic here
           
            if self.params.shared_variable[0] == IncreasedTradingVolumeStrategy.__name__:
                if self.data.low[0] < self.bollinger.bot[0]:
                    self.log(f"{IncreasedTradingVolumeStrategy.params.name} 触发的连续下跌购买")
                    if self.internal_buy():
                        # Log a message or take any action when abnormal volume is detected
                        self.log(f'当日成交量: {self.volume[0]}, {self.params.average_volume_period}天平均成交量: {self.average_volume[0]},5日均量:{self.volume_sma5[0]:.2f},10日均量:{self.volume_sma10[0]:.2f}')
                        self.log(f"昨日收盘价:{self.data.close[-1]:.2f}, 开盘价: {self.datas[0].open[0]:.2f}, 最高价: {self.datas[0].high[0]:.2f}, 最低价: {self.datas[0].low[0]:.2f}, 收盘价: {self.datas[0].close[0]:.2f}, 交易量: {self.volume[0]:.2f}")
                        self.print_kdj()
                        self.print_macd()
                        self.print_rsi()
                        self.print_sma()
                        self.print_turnover_rate(self.volume[0])
                    