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
from strategy import MACDStrategy, MACDStopLossStrategy

from data import database 
import concurrent.futures
import traceback
from loguru import logger


current_working_directory = os.getcwd()

output_path = os.path.join(current_working_directory, 'output', 'MACD-'+ datetime.now().strftime("%Y%m%d%H%M%S"))

if not os.path.exists(output_path):
    # 不存在则创建
    os.makedirs(output_path)
    


def allow_cerebro(symbol:Symbol):
    if symbol.last_price < 3:
        return False
    if symbol.last_price > 25:
        return False
    if symbol.volume < 25 * 10000:
        return False
    if symbol.market_cap is None or symbol.market_cap < 5000 * 10000:
        return False

def run_strategy(symbol):
    try:
        if allow_cerebro(symbol) == False:
            return symbol, 'allow_cerebro == false'
        # Create cerebro instance for each symbol
        cerebro = bt.Cerebro()
        log_file_path = os.path.join(output_path, f'{symbol.symbol}-MACDStrategy.log')
        cerebro.addstrategy(MACDStrategy, start_date= start_datetime.date, end_date=datetime.now().date, log_file_path = log_file_path)
        # log_file_path = os.path.join(output_path, f'{symbol.symbol}-MACDStopLossStrategy.log')
        # cerebro.addstrategy(MACDStopLossStrategy, start_date= start_datetime.date, end_date=datetime.now().date, log_file_path = log_file_path)
        
        datapath = os.path.join(current_working_directory, f'historical_data/1d/{symbol.symbol}.csv')
        if not os.path.exists(datapath):
            return symbol.symbol, None

        existing_data = pd.read_csv(datapath, parse_dates=['Date'], index_col='Date')
        print(symbol.symbol)
        if existing_data is None or existing_data.empty:
            return symbol ,'empty'

        existing_data.index = pd.to_datetime(existing_data.index, utc=True, errors='coerce')

        # Create data source
        data = bt.feeds.PandasData(dataname=existing_data)
        cerebro.adddata(data)

        cerebro.broker.setcommission(commission=0.0001)  # Assuming 0.1% commission on each trade
        cerebro.broker.set_slippage_fixed(fixed=0.01)  # Assuming 0.01 price slippage on each trade
        cerebro.broker.setcash(100000.0)  # Set initial cash
        
        # Run the strategy
        results = cerebro.run()
        # Print the returns for each strategy
        for i, strategy in enumerate(results):
            ret = strategy.broker.getvalue() / strategy.broker.startingcash - 1
            if os.path.exists(log_file_path):
                    with open(log_file_path, 'a') as f:
                        f.write(f"Strategy {i + 1} - Final Portfolio Value: {strategy.broker.getvalue():.2f}, Returns: {ret:.2%}")
                        # f.write(f'最终投资组合收益:{symbol.symbol}: 收益:{cerebro.broker.getvalue()-100000.0}, 收益率:{((cerebro.broker.getvalue()-100000)/100000)*100}%\n')
           
        
        # Return the final portfolio value
    except Exception as e:
        traceback.print_exc()
        return symbol, e
    return symbol, cerebro.broker.getvalue()

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Backtest trading strategies on historical data.')
    parser.add_argument('--symbol', nargs='+', help='Specify one or more symbols to filter (space-separated)')
    args = parser.parse_args()

    database.global_init("edge.db")

    os.chdir("./")  # 日志写入地址
    logger.add("./logs/log_{time}.log", rotation="1 day", retention="7 days")
    logger.add("./logs/error/log_{time}.log", rotation="1 day", level='ERROR',retention="7 days")

    
    symbols = []
    # Get all symbols
    with database.create_session() as db_sess:
        if args.symbol:
            symbols = [get_by_symbol(db_sess, s, "US") for s in args.symbol]
        else:
            symbols = getAll(db_sess)
      
   
    current_datetime = datetime.now()
    
    start_datetime = datetime.now() - timedelta(days=330)

    with concurrent.futures.ThreadPoolExecutor(max_workers= 100) as executor:
        futures = [executor.submit(run_strategy, symbol) for symbol in symbols]

        # Iterate over completed futures
        for future in concurrent.futures.as_completed(futures):
            symbol, result_or_exception = future.result()

            if isinstance(result_or_exception, Exception):
                print(f"Exception occurred for symbol {symbol.symbol}: {result_or_exception}")
                # Handle the exception as needed
           