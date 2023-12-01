# 导入所需模块
from __future__ import (absolute_import, division, print_function, unicode_literals)
import datetime  # 日期时间模块
import os.path  # 路径模块
import pandas as pd
# 导入backtrader平台
import backtrader as bt
from data.service.symbol_service import getAll, get_by_symbol
from datetime import datetime, timedelta
from data.model.t_symbol import Symbol
import argparse
from strategy.GreedyStrategy import GreedyStrategy

from strategy.KeltnerChannelStrategy import KeltnerChannelStrategy
from strategy.GridStrategy import GridStrategy
from strategy import MACDStrategy 
from data import database 
import concurrent.futures
import traceback

current_working_directory = os.getcwd()

output_path = os.path.join(current_working_directory, 'output', datetime.now().strftime("%Y%m%d%H%M%S"))

if not os.path.exists(output_path):
    # 不存在则创建
    os.makedirs(output_path)
    
    
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
      
        # 在TestStrategy类中添加以下方法
    def calculate_and_log_volume_averages(self):
         # Check if there is enough data for the specified periods
        if len(self.data.volume) < 100:
            return

        # Convert the data to a Pandas DataFrame for easier manipulation
        df = pd.DataFrame({
            'volume': self.data.volume.get(ago=0, size=len(self.data.volume)),
        })

        # Calculate moving averages
        df['avg_vol_10'] = df['volume'].rolling(window=10).mean()
        df['avg_vol_30'] = df['volume'].rolling(window=30).mean()
        df['avg_vol_100'] = df['volume'].rolling(window=100).mean()

        # Drop NaN values introduced by the rolling mean calculation
        df = df.dropna()

        # Convert the values back to the original scale (multiply by 10,000)
        current_vol = self.data.volume[0]
        avg_volume_10 = df['avg_vol_10'].iloc[-1]
        avg_volume_30 = df['avg_vol_30'].iloc[-1]
        avg_volume_100 = df['avg_vol_100'].iloc[-1]

        # 同时大于 30天以及 100天的平均成交量 ,并且是前一天成交量的3倍以上
         # 获取当前日期
        date = self.datas[0].datetime.datetime(0)

        # Check if the date is within the last year
        one_year_ago = datetime.now() - timedelta(days=30)
        if date >= one_year_ago:
            # Check if additional conditions are met
            if avg_volume_10 > avg_volume_30 and avg_volume_10 > avg_volume_100 and current_vol /avg_volume_10  > 2 and current_vol > 200000:
                # 打印日志
                self.log(f'日期: {date}, 当前成交量: {current_vol:.0f}, 10天平均成交量: {avg_volume_10:.0f}, 30天平均成交量: {avg_volume_30:.2f}, 100天平均成交量: {avg_volume_100:.2f}')
    
    
    
    def next(self):
        # 调用计算和记录平均成交量的方法
        self.calculate_and_log_volume_averages()
   


def allow_cerebro(symbol:Symbol):
    if symbol.last_price < 1:
        return False
    if symbol.volume < 50 * 10000:
        return False
    if symbol.market_cap is None or symbol.market_cap < 1000 * 10000:
        return False

def run_strategy(symbol):
    if allow_cerebro(symbol) == False:
        return
    
    
    # Create cerebro instance for each symbol
    cerebro = bt.Cerebro()
    log_file_path = os.path.join(output_path,f'{symbol.symbol}.log')
    cerebro.addstrategy(MACDStrategy, start_date= start_datetime.date, end_date=datetime.now().date, log_file_path = log_file_path)
    
    datapath = os.path.join(current_working_directory, f'historical_data/1d/{symbol.symbol}.csv')
    if not os.path.exists(datapath):
        return symbol.symbol, None

    existing_data = pd.read_csv(datapath, parse_dates=['Date'], index_col='Date')
    print(symbol.symbol)
    if existing_data is None or existing_data.empty:
        return

    existing_data.index = pd.to_datetime(existing_data.index, utc=True, errors='coerce')

    # Create data source
    data = bt.feeds.PandasData(dataname=existing_data)
    cerebro.adddata(data)

    cerebro.broker.setcommission(commission=0.0001)  # Assuming 0.1% commission on each trade
    cerebro.broker.set_slippage_fixed(fixed=0.01)  # Assuming 0.01 price slippage on each trade
    cerebro.broker.setcash(100000.0)  # Set initial cash
    
    # Run the strategy
    cerebro.run()

    with open(log_file_path, 'a') as f:
        f.write(f'最终投资组合收益:{symbol.symbol}: 收益:{cerebro.broker.getvalue()-100000.0}, 收益率:{((cerebro.broker.getvalue()-100000)/100000)*100}%\n')
    # Return the final portfolio value
    return

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
      
   
    current_datetime = datetime.now()
    
    start_datetime = datetime.now() - timedelta(days=730)

    with concurrent.futures.ThreadPoolExecutor(max_workers= 100) as executor:
        futures = [executor.submit(run_strategy, symbol) for symbol in symbols]

        # Iterate over completed futures
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                # Process the result if needed
            except Exception as e:
                traceback.print_exc()
                print(f"Exception occurred: {e}")
                # Handle the exception as needed