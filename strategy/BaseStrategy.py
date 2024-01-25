from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt

from typing import Dict, Any

class BaseStrategy(bt.Strategy):
    params = (
        ("name", None),
        ("symbol", None),
        ("shared_variable", [False]),
        ("start_date", None),
        ("end_date", None),
        ("percent_of_cash", 0.9),
        ("log_file_path", None),
        ("period", 9),
        ("k_period", 3),
        ("d_period", 3),
        ("sell_cross", True),  # 是否根据死叉卖出
        ("sell_gain_percentage", 0.20),  # 涨幅达到20%时卖出
        ("rsi_overbought", 70),  # RSI超买阈值
        ("rsi_oversold", 30),  # RSI超卖阈值
        ("sell_cross", True),  # 是否根据死叉卖出
    )
    
    def is_decline(self):
        return self.data_close < self.data_open and (self.data_close[0] - self.data_close[-1])/ self.data_close[-1] < 0.02

    def get_params(self):
        return self.convert_params_to_dict()
    
    def __init__(self, parameters = None):
        # Set UI modified parameters
        if parameters != None:
            for parameterName, parameterValue in parameters.items():
                setattr(self.params, parameterName, parameterValue)
                
        self.order = None  # 用于存储订单对象的属性
          # Add your MACD indicator here
        self.trade = None
        self.macd = bt.indicators.MACD()
        self.rsi = bt.indicators.RSI(self.datas[0])
        self.buy_date_data = None
        self.sell_date_data = None
        self.last_sell_day = None
        
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
        
        
        self.volume_sma5 = bt.indicators.SimpleMovingAverage(self.data.volume, period=5)
        self.volume_sma10 = bt.indicators.SimpleMovingAverage(self.data.volume, period=10)
        self.volume_sma30 = bt.indicators.SimpleMovingAverage(self.data.volume, period=30)
  
        self.SMA_5 = bt.indicators.SimpleMovingAverage(self.data.close, period=5)
        self.SMA_10 = bt.indicators.SimpleMovingAverage(self.data.close, period=10)
        self.SMA_15 = bt.indicators.SimpleMovingAverage(self.data.close, period=15)
        self.SMA_30 = bt.indicators.SimpleMovingAverage(self.data.close, period=30)
        self.SMA_60 = bt.indicators.SimpleMovingAverage(self.data.close, period=60)
   
    
    def check_allow_sell_or_buy(self):
        if self.params.start_date() and self.params.end_date():
            current_date = self.data.datetime.date(0)
            return self.params.start_date() <= current_date <= self.params.end_date()
        return True
    
    def internal_buy(self):
        if not self.check_allow_sell_or_buy():
            return False
        
        cash_to_spend = self.broker.get_cash() * self.params.percent_of_cash
       
        if cash_to_spend <= 0:
            return False

        # Consider commission and slippage in the size calculation
        commission_info = self.broker.getcommissioninfo(self.data)
        commission = commission_info.getcommission(self.data.close[0], self.data.volume[0])
        buy_value= (cash_to_spend - commission) / self.data.close[0]
       
        if buy_value <= 0:
            return False
        # self.order = self.buy(size=int(buy_value), price = self.data.close[0], exectype = bt.Order.Market )
        self.order = self.buy(size=int(buy_value), price=self.data.close[0], exectype=bt.Order.Market)
        self.buy_date_data = {
                    'date': self.datas[0].datetime.date(0),
                    'open': self.datas[0].open[0],
                    'high': self.datas[0].high[0],
                    'low': self.datas[0].low[0],
                    'close': self.datas[0].close[0],
                    'volume': self.datas[0].volume[0],
                }
        return True
        
        
    def internal_sell(self):
        if not self.check_allow_sell_or_buy():
            return
        position_size = self.position.size
        if position_size <= 0:
            return

        self.sell_date_data = {
                    'date': self.datas[0].datetime.date(0),
                    'open': self.datas[0].open[0],
                    'high': self.datas[0].high[0],
                    'low': self.datas[0].low[0],
                    'close': self.datas[0].close[0],
                    'volume': self.datas[0].volume[0],
                }
        self.sell(size= position_size)
        self.last_sell_day = self.datas[0].datetime.date(0)
        return True
    
    def notify_order(self, order):
        self.order = order
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            execution_date = bt.num2date(order.executed.dt).strftime('%Y-%m-%d')
            if order.isbuy():
                self.last_sell_day = None
                self.log(f"买入日期: {execution_date}, 开盘价: {self.buy_date_data['open']:.2f}, 最高价: {self.buy_date_data['high']:.2f}, 最低价: {self.buy_date_data['low']:.2f}, 收盘价: {self.buy_date_data['close']:.2f}, 交易量: {self.buy_date_data['volume']:.2f}")
                self.log(f"买入完成: 价格 {order.executed.price:.2f},数量 {order.executed.size:.0f},总金额:{order.executed.value:.2f},手续费{order.executed.comm:.2f}")
                
            elif order.issell():
                self.log(f"卖出日期: {execution_date}, 开盘价: {self.sell_date_data['open']:.2f}, 最高价: {self.sell_date_data['high']:.2f}, 最低价: {self.sell_date_data['low']:.2f}, 收盘价: {self.sell_date_data['close']:.2f}, 交易量: {self.sell_date_data['volume']:.2f}")
                self.log(f"卖出完成: 价格 {order.executed.price:.2f},数量 {order.executed.size:.0f},手续费{order.executed.comm:.2f}")
        # Check if an order has been canceled/rejected
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/拒绝')

       
        
    def print_macd(self):
        self.log(f'MACD DIF:{self.macd.macd[0]}, DEA:{self.macd.signal[0]}, MACD:{self.macd.macd - self.macd.signal}')
    
    def print_kdj(self):
        self.log(f'K:{self.K[0]:.3f},D:{self.D[0]:.3f},J:{self.J[0]:.3f}')
    
    def print_rsi(self):
        self.log(f'RSI1:{self.rsi[0]:.3f}')
        
    def print_turnover_rate(self, volume:int):
        if self.params.symbol.shares_outstanding and self.params.symbol.shares_outstanding != 0:
            self.log(f'换手率:{(volume*100)/self.params.symbol.shares_outstanding:.2f}')
    
    def print_bolling(self):
        self.log("布林线: 上轨: {:.2f}, 中轨: {:.2f}, 下轨: {:.2f}".format(
                        self.bollinger.lines.top[0],
                        self.bollinger.lines.mid[0],
                        self.bollinger.lines.bot[0]
                    ))
        
    def print_sma(self):
            self.log("均线: 5天: {:.2f}, 10天: {:.2f}, 15天: {:.2f}, 30天: {:.2f}, 60天:{:.2f}".format(
                        self.SMA_5[0],
                        self.SMA_10[0],
                        self.SMA_15[0],
                        self.SMA_30[0],
                        self.SMA_60[0]
                    ))

    def calculate_profit_percentage(self):
        if self.position:
            buy_price = self.position.price
            current_high_price = self.data.high[0]
            return (current_high_price - buy_price) / buy_price
        return 0.0
    
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt.isoformat(), txt))
        
        if self.params.log_file_path:
            with open(self.params.log_file_path, 'a') as f:
                f.write(f"{dt.isoformat()}, {self.params.name}, {txt}\n")


    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.trade = trade
        # print(trade)
        self.log(f'交易盈亏: 毛盈亏 {trade.pnl:.2f}, 净盈亏 {trade.pnlcomm:.2f}')

    # def next(self):
    #     self.auto_sell()
        
    # # 自动卖出交易，根据持仓以及卖出信号进行卖出操作
    # def auto_sell(self):