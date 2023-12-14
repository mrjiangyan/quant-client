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

from data import database 
import concurrent.futures
import traceback
from loguru import logger
import strategy as Strategy


current_working_directory = os.getcwd()
days = 5

def allow_cerebro(symbol:Symbol, period:str ):
    if not (1 < symbol.last_price < 200):
        return False
    
    # 成交量小于50万股的就不考虑
    if period == '1d' and symbol.volume < 10 * 10000:
        return False
     # 股票数量小于250万股的就不考虑
    if symbol.market_cap is None or symbol.market_cap/symbol.last_price < 250 * 10000:
        return False

def run_strategy(symbol: Symbol, period:str):
    try:
        if allow_cerebro(symbol, period) == False:
            return symbol, None
        # Create cerebro instance for each symbol
        
        datapath = os.path.join(current_working_directory, f'historical_data/{period}/{symbol.symbol}.csv')
        if not os.path.exists(datapath):
            return symbol.symbol, None

        existing_data = pd.read_csv(datapath, parse_dates=['Date'], index_col='Date')
           
        if existing_data is None or existing_data.empty:
            return symbol , None
        
        existing_data = (existing_data.loc[(existing_data['Volume'] != 0) & (existing_data['Volume'].notna())]
                .loc[(existing_data['Open'] != 0) & (existing_data['Open'].notna())]
                .loc[(existing_data['Close'] != 0) & (existing_data['Close'].notna())])
        
        if len(existing_data) < 50:
                return symbol , None
        print(symbol.symbol)
        existing_data.index = pd.to_datetime(existing_data.index, utc=True, errors='coerce')
        
        enums = enumerate([Strategy.BollingerStrategy, Strategy.MacdTrendStrategy, Strategy.MacdDoubleBottomStrategy,Strategy.MacdStrategy])
        enums = enumerate([Strategy.BollingerStrategy])
        # enums = enumerate([Strategy.BollingerStrategy, Strategy.MACDStrategy, Strategy.MacdCrossStrategy])
        for i, strategy_cls in enums:
             # 创建策略实例
            cerebro = bt.Cerebro()
          
            # 创建日志文件路径
            log_file_path = os.path.join(output_path, f'{symbol.symbol}-{strategy_cls.__name__}.log')
            
            # 将策略实例添加到Cerebro中
            cerebro.addstrategy(strategy_cls, start_date=start_datetime.date, end_date=datetime.now().date, log_file_path=log_file_path)
              # Create data source
            data = bt.feeds.PandasData(dataname=existing_data)
            cerebro.adddata(data)

            cerebro.broker.setcommission(commission=0.0001)  # Assuming 0.1% commission on each trade
            cerebro.broker.set_slippage_fixed(fixed=0.01)  # Assuming 0.01 price slippage on each trade
            cerebro.broker.setcash(1000.0)  # Set initial cash
            # 运行策略
            cerebro.run()

            # 获取统计信息
            ret = cerebro.broker.getvalue() / cerebro.broker.startingcash - 1
            
            if os.path.exists(log_file_path):
                    with open(log_file_path, 'a') as f:
                        f.write(f"收益总额: {cerebro.broker.getvalue():.2f}, Returns: {ret:.2%}")
          
       
        
        # Plot the result
        #cerebro.plot(style='bar')
        # Return the final portfolio value
    except Exception as e:
        traceback.print_exc()
        logger.error(symbol.symbol)
        return symbol, e
    return symbol, cerebro.broker.getvalue()

def analyze_returns(symbol_returns):
    # Dictionary to store individual returns for each symbol
    symbol_individual_returns = {}

    for symbol, returns in symbol_returns.items():
        if isinstance(returns, Exception):
            print(f"Exception occurred for symbol {symbol.symbol}: {returns}")
            # Handle the exception as needed
        elif returns != 1000.0:
            revenue = returns - 1000
            symbol_individual_returns[symbol.symbol] = revenue

    # 对 symbol_individual_returns 字典按照值进行排序
    sorted_returns = sorted(symbol_individual_returns.items(), key=lambda x: x[1], reverse=True)

    
    log_file_path = os.path.join(output_path, f'summary.log')
    with open(log_file_path, 'a') as f:
        print("\n每个Symbol的收益金额:")
        for symbol, individual_return in sorted_returns:
            content= f"{symbol}: {individual_return:.2f}"
            print(content)
            f.write(content)
                   
          

if __name__ == '__main__':
    

    input_symbol = None
    input_symbol = input(f"请输入需要回测的证券代码以空格分割（默认为全部）: ") or input_symbol

    # default_macd_level = '2'
    # macd_level = input(f"请输入买入点要求的macd等级（默认为 {default_macd_level}）: ") or default_macd_level

    period = '1d'
    period = input(f"请输入K线数据类型（默认为 {period}）: ") or period

    default_days = 5
    default_days = input(f"请输入回测的天数（默认为 {days}）: ") or default_days

    days = int(default_days)
        
    output_path = os.path.join(current_working_directory, 'output', f'MACD-{period}-{datetime.now().strftime("%Y-%m-%d-%H-%M")}' )

    if not os.path.exists(output_path):
        # 不存在则创建
        os.makedirs(output_path)
    
    database.global_init("edge.db")
 
    symbols = []
    # Get all symbols
    with database.create_session() as db_sess:
        if input_symbol:
            symbols = [get_by_symbol(db_sess, s, "US") for s in input_symbol.split(' ')]
        else:
            symbols = getAll(db_sess)
      
    current_datetime = datetime.now()
    
    start_datetime = datetime.now() - timedelta(days=days)

    symbol_returns = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(run_strategy, symbol, period ) for symbol in symbols]

        # Iterate over completed futures
        for future in concurrent.futures.as_completed(futures):
            symbol, result_or_exception = future.result()

            if isinstance(result_or_exception, Exception):
                symbol_returns[symbol] = result_or_exception
            elif result_or_exception:
                symbol_returns[symbol] = result_or_exception  # Replace with the actual return value from your strategy

    # Analyze and display returns
    analyze_returns(symbol_returns)