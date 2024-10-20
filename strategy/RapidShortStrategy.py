from __future__ import (absolute_import, division, print_function, unicode_literals)
from .BaseStrategy import BaseStrategy
from loguru import logger

class RapidShortStrategy(BaseStrategy):
    params = (
        ("name", '快速1～2根阳线大幅上涨股票卖空策略'), 
        ('lookback_period', 10),  # 前10天
        ('amplitude_threshold', 15),  # 振幅不超过15%
        ('daily_return_threshold', 0.25),  # 涨幅超过25%
        ('bollinger_upper_threshold', 0.18),  # 超过布林线上轨18%
        ('exit_return_threshold', 0.12),  # 第二天收益超过10%
        ('min_volume', 100*10000),  # 最小成交量不能低于50万
        ('min_price', 2),  # 最低价格不能低于2元，否则实际能够卖空的标的也会很少
        ('max_price', 20),  # 最高价格不能高于20元，否则大概率不会出现大幅下跌
        ('small_cap_turnover_rate', 2),  # 总股本小于1000万的换手率要超过200%
        ('medium_cap_turnover_rate', 1),  # 总股本在1000万到5000万之间的换手率不能低于100%
        ('large_cap_turnover_rate', 0.5),  # 总股本在5000万到1亿之间的换手率不能低于50%
        ('huge_cap_turnover_rate', 0.2),  # 总股本超过1亿的换手率不能低于20%
    )

    def __init__(self, *argv):
        # used to modify parameters
        super().__init__(argv[0])
        self.is_short = True
        self.sell_signal = False
        
    def next(self): 
        if not self.check_allow_sell_or_buy():
            return
        if len(self) > self.params.lookback_period:
            # 计算振幅
            # amplitude = (self.data.close[0] - min(self.data.low.get(size=self.params.lookback_period))) / min(self.data.low.get(size=self.params.lookback_period))
            # logger.info(f'{self.datas[0].datetime.datetime(0)}', amplitude)
            # if (amplitude <= self.params.amplitude_threshold and 
            if    (self.data.volume[0] > self.params.min_volume
                and  self.params.max_price > self.data.close[0] > self.params.min_price
                and (self._check_turnover_rate(self.data.volume[0]))
                ):
                # 计算当日涨幅
                daily_return = (self.data.high[0] - self.data.close[-1]) / self.data.close[-1]
                if (daily_return > self.params.daily_return_threshold and 
                    self.data.high[0] > self.bollinger.lines.top[0] * (1 + self.params.bollinger_upper_threshold)):
                    # 进行卖空交易
                    if self.data.low[0] > self.data.close[-1]:
                        self.log('发出卖空信号')
                        if self.internal_sell(): 
                            self.sell_signal = False
                    else:
                        self.sell_signal = True
            elif self.sell_signal  and self.data.high[0] > self.data.high[-1]:
                if self.internal_sell(): 
                    self.sell_signal = False
                
        # 只要收益超过10%就可以考虑卖出 
        if self.sellprice > 0 and (self.sellprice  - self.data.low[0]) / self.sellprice > self.params.exit_return_threshold:
            self.internal_buy()
            self.sell_signal = False

    
    def _check_turnover_rate(self, volume):
        # 获取总股本
        total_shares_outstanding = self.params.symbol.shares_outstanding if self.params.symbol.shares_outstanding else 0
        if total_shares_outstanding == 0:
            return True
        turnover_rate = self.turnover_rate(volume)
        
        if total_shares_outstanding < 1000 * 10000:
            return turnover_rate > self.params.small_cap_turnover_rate 
        elif 1000 * 10000 <= total_shares_outstanding < 5000 * 10000:
            return turnover_rate >= self.params.medium_cap_turnover_rate
        elif 5000 * 10000 <= total_shares_outstanding < 10000 * 10000:
            return turnover_rate >= self.params.large_cap_turnover_rate
        elif total_shares_outstanding >= 10000 * 10000:
            return turnover_rate >= self.params.huge_cap_turnover_rate
