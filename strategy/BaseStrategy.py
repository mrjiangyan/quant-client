from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt

class BaseStrategy(bt.Strategy):
    params = (
        ("symbol", ''),
        ("start_date", None),
        ("end_date", None),
        ("percent_of_cash", 0.6),
        ("log_file_path", None),
        ("period", 9),
        ("k_period", 3),
        ("d_period", 3),
    )
     
    def __init__(self):
        self.name = None  # 父类中定义的属性
          # Add your MACD indicator here
        self.macd = bt.indicators.MACD()

        # Add Bollinger Bands
        self.bollinger = bt.indicators.BollingerBands()
        
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
        
   
    
    def check_allow_sell_or_buy(self):
        if self.params.start_date() and  self.params.end_date():
            current_date = self.data.datetime.date(0)
            return self.params.start_date() <= current_date <= self.params.end_date()
        return True
    
    def internal_buy(self):
        if not self.check_allow_sell_or_buy():
            return False
        
        cash_to_spend = self.broker.get_cash() * self.params.percent_of_cash
        if cash_to_spend <= 0:
            return False

        size = cash_to_spend / self.data.close[0]
        if size <= 0:
            return False
        date = self.datas[0].datetime.datetime(0)
        open_price = self.datas[0].open[0]
        high_price = self.datas[0].high[0]
        low_price = self.datas[0].low[0]
        close_price = self.datas[0].close[0]
        volume = self.datas[0].volume[0]
        cash_to_spend = self.broker.getvalue() * self.params.percent_of_cash
        self.buy(size=size)
        self.log('买入日期: %s, 开盘价: %.2f, 最高价: %.2f, 最低价: %.2f, 收盘价: %.2f, 交易量: %.2f' %
                    (date.strftime('%Y-%m-%d %H:%M'), open_price, high_price, low_price, close_price, volume))
        self.log(f"买入完成: 价格 {self.data.close[0]:.2f},数量 {size:.0f},总金额:{self.data.close[0]*size}")
        return True
        
    def internal_sell(self):
        if not self.check_allow_sell_or_buy():
            return
        
        
        position_size = self.position.size
        if position_size <= 0:
            return

        self.sell(size= position_size)
        date = self.datas[0].datetime.datetime(0)
        open_price = self.datas[0].open[0]
        high_price = self.datas[0].high[0]
        low_price = self.datas[0].low[0]
        close_price = self.datas[0].close[0]
        volume = self.datas[0].volume[0]
        self.log('卖出日期: %s, 开盘价: %.2f, 最高价: %.2f, 最低价: %.2f, 收盘价: %.2f, 交易量: %.2f' %
                    (date.strftime('%Y-%m-%d %H:%M'), open_price, high_price, low_price, close_price, volume))
        self.log(f"卖出完成: 价格 {self.data.close[0]:.2f},数量 {self.position.size:.0f}")
        return True
    # def notify_order(self, order):
    #     if order.status in [order.Submitted, order.Accepted]:
    #         return

    #     # Check if an order has been canceled/rejected
    #     elif order.status in [order.Canceled, order.Margin, order.Rejected]:
    #         self.log('订单取消/拒绝')

    #     self.order = None
    
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt.isoformat(), txt))
        
        if self.params.log_file_path:
            with open(self.params.log_file_path, 'a') as f:
                f.write(f"{dt.isoformat()}, {self.name}, {txt}\n")


    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        # self.log(f'交易盈亏: 毛盈亏 {trade.pnl}, 净盈亏 {trade.pnlcomm}')

        