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
        self.order = None  # 用于存储订单对象的属性
        self.name = None  # 父类中定义的属性
          # Add your MACD indicator here
        self.macd = bt.indicators.MACD()
        self.buy_date_data = None
        self.sell_date_data = None
        # Add Bollinger Bands
        self.bollinger = bt.indicators.BollingerBands()
        
        self.high_nine = bt.indicators.Highest(self.data.high, period=self.params.period)
        # 9个交易日内最低价
        self.low_nine = bt.indicators.Lowest(self.data.low, period=self.params.period)
        
        # 计算rsv值
        self.rsv = 100 * bt.DivByZero(
            self.data.close - self.low_nine, self.high_nine - self.low_nine, zero=0
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
        
        cash_available = self.broker.get_cash()
        cash_to_spend = self.broker.get_cash() * self.params.percent_of_cash
        if cash_to_spend <= 0:
            return False

        # Consider commission and slippage in the size calculation
        commission_info = self.broker.getcommissioninfo(self.data)
        commission = commission_info.getcommission(self.data.close[0], self.data.volume[0])
        buy_value= (cash_to_spend - commission) / self.data.close[0]
       
        if buy_value <= 0:
            return False
        self.buy_date_data = {
                    'date': self.datas[0].datetime.datetime(0),
                    'open': self.datas[0].open[0],
                    'high': self.datas[0].high[0],
                    'low': self.datas[0].low[0],
                    'close': self.datas[0].close[0],
                    'volume': self.datas[0].volume[0],
                }
        self.order = self.buy(size=int(buy_value))
        return True
        
        
    def internal_sell(self):
        if not self.check_allow_sell_or_buy():
            return
        position_size = self.position.size
        if position_size <= 0:
            return

        self.sell_date_data = {
                    'date': self.datas[0].datetime.datetime(0),
                    'open': self.datas[0].open[0],
                    'high': self.datas[0].high[0],
                    'low': self.datas[0].low[0],
                    'close': self.datas[0].close[0],
                    'volume': self.datas[0].volume[0],
                }
        self.sell(size= position_size)
        
        return True
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            execution_date = bt.num2date(order.executed.dt).strftime('%Y-%m-%d')
            if order.isbuy():
                self.log(f"买入日期: {execution_date}, 开盘价: {self.buy_date_data['open']:.2f}, 最高价: {self.buy_date_data['high']:.2f}, 最低价: {self.buy_date_data['low']:.2f}, 收盘价: {self.buy_date_data['close']:.2f}, 交易量: {self.buy_date_data['volume']:.2f}")
                self.log(f"买入完成: 价格 {order.executed.price:.2f},数量 {order.executed.size:.0f},总金额:{order.executed.value:.2f}")
            elif order.issell():
                self.log(f"卖出日期: {execution_date}, 开盘价: {self.sell_date_data['open']:.2f}, 最高价: {self.sell_date_data['high']:.2f}, 最低价: {self.sell_date_data['low']:.2f}, 收盘价: {self.sell_date_data['close']:.2f}, 交易量: {self.sell_date_data['volume']:.2f}")
                self.log(f"卖出完成: 价格 {order.executed.price:.2f},数量 {order.executed.size:.0f}")
        # Check if an order has been canceled/rejected
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/拒绝')

        self.order = None
    
    def calculate_profit_percentage(self):
        if self.position:
            buy_price = self.position.price
            current_price = self.data.close[0]
            return (current_price - buy_price) / buy_price
        return 0.0
    
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

        