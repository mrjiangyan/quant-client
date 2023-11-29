# 导入所需模块
from __future__ import (absolute_import, division, print_function, unicode_literals)
import datetime  # 日期时间模块
import os.path  # 路径模块
import pandas as pd
# 导入backtrader平台
import backtrader as bt
from data.service.symbol_service import getAll, get_by_symbol
from data import database
from datetime import datetime
import argparse

# 创建策略
class TestStrategy(bt.Strategy):

    params = (
        ("percent_of_cash", 0.9),  # 每次交易使用的现金比例
    )
    
    def log(self, txt, dt=None):
        ''' 日志函数 '''
        dt = dt or self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # 保留对数据序列中`close`线的引用
        self.dataclose = self.datas[0].close
        # 添加MACD指标
        self.macd = bt.indicators.MACD(self.data.close)
        self.current_position = None  # To keep track of the current position
        self.buy_price = None
        self.sell_price = None
        
    def next(self):
        date = self.datas[0].datetime.datetime(0)
        open_price = self.datas[0].open[0]
        high_price = self.datas[0].high[0]
        low_price = self.datas[0].low[0]
        close_price = self.datas[0].close[0]
        volume = self.datas[0].volume[0]
        # Buy logic: Check for MACD crossover below the zero line
        dif = self.macd.lines.macd[0]
        
        dea = self.macd.lines.signal[0]
        if dif < -0.5 and  dif > dea and dif < 0 and dif > self.macd.lines.macd[-1] and self.macd.lines.macd[-1] < self.macd.lines.signal[-1]:
            # target_date_str = '2023-11-24T00:00:00'
            # target_date = datetime.strptime(target_date_str, '%Y-%m-%dT%H:%M:%S')
            # and self.datas[0].datetime.datetime(0) == target_date      
            if self.current_position != 'long' :
                #self.datas[0].datetime.datetime(0) == '2023-11-24T00:00:00'
                self.log('日期: %s, 开盘价: %.2f, 最高价: %.2f, 最低价: %.2f, 收盘价: %.2f, 交易量: %.2f' %
                    (date, open_price, high_price, low_price, close_price, volume))
                # 记录数据序列的收盘价
               # Place the buy order
                # 计算购买数量
                cash_to_spend = self.broker.getvalue() * self.params.percent_of_cash
                size = cash_to_spend / self.data.close[0]

                # 下单买入
                self.buy(size=size)
                # Log the buy signal details
                self.log(f'Buy Signal: {self.dataclose[0]}, MACD: {self.macd.macd[0]}, DIF: {self.macd.lines.macd[0]}, DEA: {self.macd.lines.signal[0]}')
                self.log(f"买入完成: 价格 {self.data.close[0]},数量 {size}")
              
                self.current_position = 'long'

        # Sell logic: Check for MACD crossunder above the zero line
        elif dif < dea and dif > 0 and dif < self.macd.lines.macd[-1] and self.macd.lines.macd[-1] > self.macd.lines.signal[-1]:
            if self.current_position != 'short': 
                    self.log('日期: %s, 开盘价: %.2f, 最高价: %.2f, 最低价: %.2f, 收盘价: %.2f, 交易量: %.2f' %
                        (date.strftime('%Y-%m-%d %H:%M'), open_price, high_price, low_price, close_price, volume))
                    # Log the sell signal details
                    self.log(f'Sell Signal: {self.dataclose[0]}, MACD: {self.macd.macd[0]}, DIF: {self.macd.lines.macd[0]}, DEA: {self.macd.lines.signal[0]}')
                    # Place the sell order
                     # 下单卖出
                    self.sell(size=self.position.size)
                    self.current_position = 'short'
                    # 在每次卖出完成后添加一行日志输出
                    self.log(f"卖出完成: 价格 {self.data.close[0]}, 成本 {self.broker.get_cash()} 数量 {self.position.size}")

                    # 计算并打印交易盈亏
                    profit_loss = self.position.size * (self.data.close[0] - self.position.price) 
                    self.log(f"交易盈亏: 毛盈亏 {profit_loss}, 净盈亏 {self.broker.getvalue() - self.broker.startingcash}")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        # Check if an order has been canceled/rejected
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/拒绝')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log(f'交易盈亏: 毛盈亏 {trade.pnl}, 净盈亏 {trade.pnlcomm}')

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Backtest trading strategies on historical data.')
    parser.add_argument('--symbol', nargs='+', help='Specify one or more symbols to filter (space-separated)')
    args = parser.parse_args()

    database.global_init("edge.db")
    # Create the full path for the download file in the current directory
    download_path = os.path.join(os.getcwd(), 'historical_data')
    # Create the directory if it doesn't exist
    os.makedirs(download_path, exist_ok=True)

    symbols = []
    # Get all symbols
    with database.create_session() as db_sess:
        if args.symbol:
            symbols = [get_by_symbol(db_sess, s, "US") for s in args.symbol]
        else:
            symbols = getAll(db_sess)
      
     # 数据在样本的子文件夹中。需要找到脚本所在的位置
        # 因为它可以从任何地方调用
    current_working_directory = os.getcwd()
    
    count = 0
    max = 0;
    min= 0;  
    current_datetime = datetime.now()
    timestamp = current_datetime.strftime('%Y%m%d%H%M%S')
    winner_count = 0 ;
    for symbol in symbols:
        # 创建cerebro实体
        cerebro = bt.Cerebro()
        # 添加策略
        cerebro.addstrategy(TestStrategy)

        datapath = os.path.join(current_working_directory, f'historical_data/1d/{symbol.symbol}.csv')
        
        if os.path.exists(datapath) == False:
            continue
        
        print(symbol.symbol)
        existing_data = pd.read_csv(datapath, parse_dates=True, index_col='Date')
        existing_data.index = pd.to_datetime(existing_data.index, utc=True)
        
        print(symbol.symbol)
        if existing_data is None or existing_data.empty:
            continue
        
        print(len(existing_data))
        if len(existing_data) < 28:
            continue
        # 创建数据源
        data = bt.feeds.PandasData(dataname = existing_data)
        # 将数据源添加到Cerebro
        cerebro.adddata(data)

        cerebro.broker.setcommission(commission=0.0001)  # Assuming 0.1% commission on each trade
        cerebro.broker.set_slippage_fixed(fixed=0.01)  # Assuming 0.01 price slippage on each trade
    
        # 设置我们所需的现金起始值
        cerebro.broker.setcash(100000.0)
      
        # 运行所有
        cerebro.run()

        # 打印出最终结果
        print('最终投资组合价值：%.2f' % cerebro.broker.getvalue())

        profit = cerebro.broker.getvalue()-100000.0

        if profit > max:
            max = profit
        if profit < min:
            min = profit
        if profit > 0 :
            winner_count=winner_count+1
        count = count+1
        with open(f'output-{timestamp}.txt', 'a') as f:
            f.write(f'最终投资组合价值：{symbol.symbol}: {profit}\n')

    print(f'计算总数:{count},最高:{max}, 最低:{min}, winner_count:{winner_count}')
