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
    if not (2.5 < symbol.last_price < 50):
        return False
    
    # 成交量小于50万股的就不考虑
    if period == '1d' and symbol.volume < 50 * 10000:
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
        
        enums = enumerate([Strategy.MacdTrendStrategy, Strategy.MacdDoubleBottomStrategy,Strategy.MacdStrategy])
        # enums = enumerate([Strategy.MacdDoubleBottomStrategy])
        # enums = enumerate([Strategy.BollingerStrategy, Strategy.MACDStrategy, Strategy.MacdCrossStrategy])
        for i, strategy_cls in enums:
             # 创建策略实例
            cerebro = bt.Cerebro()
          
            print(strategy_cls.__name__)
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
                        f.write(f"Final Portfolio Value: {cerebro.broker.getvalue():.2f}, Returns: {ret:.2%}")
          
       
        
        # Plot the result
        #cerebro.plot(style='bar')
        # Return the final portfolio value
    except Exception as e:
        traceback.print_exc()
        logger.error(symbol.symbol)
        return symbol, e
    return symbol, cerebro.broker.getvalue()

def analyze_returns(symbol_returns):
    total_returns = 0
    return_count = 0

    # Dictionary to store individual returns for each symbol
    symbol_individual_returns = {}

    for symbol, returns in symbol_returns.items():
        if isinstance(returns, Exception):
            print(f"Exception occurred for symbol {symbol.symbol}: {returns}")
            # Handle the exception as needed
        elif returns == 1000.0:
            continue
        else:
            revenue = returns-1000
            total_returns += revenue
            return_count += 1
            symbol_individual_returns[symbol] = revenue

    # Calculate average return
    average_return = total_returns / return_count if return_count > 0 else 0

    
    print("\n收益分布:")
    intervals = {}
    for symbol, individual_return in symbol_individual_returns.items():
        if individual_return < 0:
            intervals.setdefault(-10, []).append(symbol.symbol)
        else:
            interval_key = int(individual_return / 1000) 
            intervals.setdefault(interval_key, []).append(symbol.symbol)

    for interval, symbols_in_interval in intervals.items():
        print(f"{interval}% - {interval + 10}%: {len(symbols_in_interval)} symbols ({', '.join(symbols_in_interval)})")

    print(f"\n交易symbol总数: {return_count}")
    print(f"Average Revenue: {average_return:.2f}")


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Backtest trading strategies on historical data.')
    parser.add_argument('--symbol', nargs='+', help='指定的证券代码')
    parser.add_argument('--macd_level', nargs='+', help='设置买入点要求的macd等级')
    parser.add_argument('--period', nargs='+', help='设置k线数据类型')
    parser.add_argument('--days', nargs='+', help='设置k线数据类型')
    args = parser.parse_args()

    period = '1d';
    if args.period:
        period = args.period[0]
        
    if args.days:
        days = int(args.days[0])
        
    output_path = os.path.join(current_working_directory, 'output', f'MACD-{period}-{datetime.now().strftime("%Y-%m-%d-%H-%M")}' )

    if not os.path.exists(output_path):
        # 不存在则创建
        os.makedirs(output_path)
    
    database.global_init("edge.db")
 
    symbols = []
    # Get all symbols
    with database.create_session() as db_sess:
        if args.symbol:
            symbols = [get_by_symbol(db_sess, s, "US") for s in args.symbol]
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