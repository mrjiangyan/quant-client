
from .BaseStrategy import BaseStrategy
import backtrader as bt
from datetime import datetime
#macd趋势分析
class MacdTrendStrategy(BaseStrategy):
    params = (
        ("name", '底部MACD金叉趋势预判策略'), 
        ("macd_level", -0.3),
        ('oversold_threshold', 40),
        ('overbought_threshold', 80),
    )
    
    def __init__(self, *argv):
            # used to modify parameters
        super().__init__(argv[0])
    
    def has_large_drawdown(self, days):    
        for i in range(-days+1, 0):
            if (self.data.close[i-1] - self.data.close[i])/self.data.close[i-1] > 0.35:
                return True

        return False

    def check_consecutive_down(self, start_idx, window_size, consecutive_days):
        # 从 start_idx 开始往前取 window_size 天记录
        data_close_slice = self.data.close.get(size=window_size, ago=start_idx)
        data_open_slice = self.data.open.get(size=window_size, ago=start_idx)
        # 判断连续下跌的天数
        down_count = 0
        for i in range(len(data_close_slice) - 1, 0, -1):
            if data_close_slice[i] < data_open_slice[i]:
                down_count += 1
                if down_count == consecutive_days:
                    return True
            else:
                down_count = 0

        return False
    
    def has_not_continuous_decline(self, days, limit_down_days):
        days = 0 
        for i in range(-days+1, 0):
            if self.data.close[i-1] > self.data.close[i]:
                days = days +1
        return days < limit_down_days
    
    def next(self):
        if not self.check_allow_sell_or_buy():
            return
        if self.position:
            sell_signal = False
            distince_days = (self.data.datetime.date(0) - self.buy_date_data['date']).days
            if not sell_signal and distince_days <= 20:
                sell_signal = self.calculate_profit_percentage() > 0.4
                if  sell_signal:
                    self.log(f'卖出涨幅20天内条件满足')
            if not sell_signal and 20 < distince_days <=30:
                sell_signal =  0 < self.calculate_profit_percentage() > 0.6
                if sell_signal:
                        self.log(f'卖出涨幅30天内涨幅条件满足')
            
            if not sell_signal and distince_days<=40:
                sell_signal = self.calculate_profit_percentage() > 0.8
                if sell_signal:
                    self.log(f'卖出涨幅40天内涨幅超过80%条件满足')
            if not sell_signal and distince_days>=40:
                sell_signal = self.calculate_profit_percentage() > 0.6
                if sell_signal:
                     self.log(f'卖出涨幅超过40天内涨幅超过60%')
            if not sell_signal and (
                self.data.close[-2] > self.bollinger.lines.top[-2] 
                and self.data.close[-1] > self.bollinger.lines.top[-1] 
                and self.data.close[0] > self.bollinger.lines.top[0] 
            ):
                sell_signal =  True
                if sell_signal:
                    self.log(f'连续三周超出布林线上轨，达成卖出条件')
            if not sell_signal and self.macd.signal[0]  > self.macd.macd[0] > 0 and self.macd.signal[-1] > self.macd.signal[0]:
                sell_signal = True
            # if sell_signal == False:
            #     sell_signal =  (self.order.executed.price - self.data.low[0])/ self.order.executed.price  > 0.08
            #     if  sell_signal:
            #         self.log(f'止损位条件满足')
            
        
            if sell_signal:
                self.internal_sell()
                self.reset()
                return
        current_date = self.data.datetime.date(0)
        if current_date > datetime.strptime('2023-12-15', '%Y-%m-%d').date():
            return
        # Check if dif is rising for three consecutive days and other conditions
        if (
            self.macd.macd[-2] < self.macd.macd[-1] < self.macd.macd[0] 
            and self.macd.macd[0] < self.macd.signal[0] < self.params.macd_level  
            and  self.macd.signal[-2] >= self.macd.signal[-1] > self.macd.signal[0] 
            # and self.macd.signal[0]-self.macd.macd[0] < 0.1
            # and not self.check_consecutive_down(0, 10, 3)
            and not self.has_large_drawdown(20)
            and self.has_not_continuous_decline(10, 6)
            and self.data.volume[0] > 1 * 10000
                and self.J[0] < self.params.oversold_threshold
                and self.params.symbol.shares_outstanding > 2500 * 10000
                ):
            # MACD line crossed above the signal line (Golden Cross) - Generate buy signal
            if not self.position and self.internal_buy():
                self.print_kdj()
                self.print_bolling()
                self.print_macd()
                self.print_sma()
                self.print_rsi()
                self.print_turnover_rate(self.data.volume[0])
  
