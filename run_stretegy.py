# 导入所需模块
from __future__ import (absolute_import, division, print_function, unicode_literals)

import datetime  # 日期时间模块
import os.path  # 路径模块
import pandas as pd
# 导入backtrader平台
import backtrader as bt
print(bt.__version__)
from data.service.symbol_service import getAll, get_by_symbol
from datetime import datetime, timedelta
from data.model.t_symbol import Symbol
from data import database 
import concurrent.futures
import traceback
from loguru import logger
import importlib
import inspect
from strategy.BaseStrategy import BaseStrategy

current_working_directory = os.getcwd()

cash = 10000.0

# 示例：假设策略类定义在名为 "strategies" 的模块中
module_name = "strategy"

def get_all_classes(module_name):
    module = importlib.import_module(module_name)
    all_classes = [obj[1] for obj in inspect.getmembers(module, inspect.isclass) if issubclass(obj[1], object) and obj[1] is not object]
    return all_classes


all_strategies = get_all_classes(module_name)

def allow_cerebro(symbol:Symbol, period:str ):
    if not (1 < symbol.last_price < 200):
        return False
    
    if symbol.compute == False:
        return False
    # 成交量小于50万股的就不考虑
    # if period == '1d' and symbol.volume < 10 * 10000:
    #     return False
     # 股票数量小于250万股的就不考虑
    # if symbol.market_cap is None or symbol.market_cap/symbol.last_price < 250 * 10000:
    #     return False
    return True

def process_strategy(symbol: Symbol, period:str, start_datetime:datetime, strategy_cls, output_path:str ):
    try:
        if allow_cerebro(symbol, period) == False:
            return symbol, None

        datapath = os.path.join(current_working_directory, 'resources', f'historical_data/{period}/{symbol.symbol}.csv')
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

         # 创建日志文件路径
        log_file_path = os.path.join(output_path, f'{symbol.symbol}.log')
        
        # 创建策略实例
        cerebro = bt.Cerebro(stdstats = False, maxcpus =None)
        # cerebro = bt.Cerebro(cheat_on_close = True)
        # cerebro.broker_set_coc(True) 
        
        shared_var = [False] 
        # 将策略实例添加到Cerebro中
        cerebro.addstrategy(strategy_cls, {}, shared_variable=shared_var, start_date= start_datetime.date, end_date=datetime.now().date, log_file_path=log_file_path, symbol = symbol)

        # Add the first strategy to the engine with the shared variable
        # cerebro.addstrategy(BuyExecutor, shared_variable=shared_var, start_date=start_datetime.date, end_date=datetime.now().date, log_file_path=log_file_path, symbol = symbol)

        cerebro.broker.setcommission(commission=0.002) 
        cerebro.broker.set_cash(cash=cash)
        cerebro.broker.set_slippage_perc(0.01)
        cerebro.broker.set_slippage_fixed(0.03)
        cerebro.broker.set_coc(True)
            # Create data source
        data = bt.feeds.PandasData(dataname=existing_data)
        cerebro.adddata(data)
        # 运行策略
        # cerebro.run(tradehistory = True)
        cerebro.run()
        
        # 获取统计信息
        ret = cerebro.broker.getvalue() / cerebro.broker.startingcash - 1
        
        if os.path.exists(log_file_path):
            with open(log_file_path, 'a') as f:
                f.write(f"账户总值: {cerebro.broker.getvalue():.2f}, Returns: {ret:.2%}\n")
           
          
    except Exception as e:
        traceback.print_exc()
        logger.error(symbol.symbol)
        return symbol, e
    return symbol, cerebro.broker.getvalue()

 # 获取参数

def get_user_input_for_params(strategy_cls:BaseStrategy):

   # 假设 strategy_cls 是 BaseStrategy
    strategy_instance = strategy_cls()

    # 然后你可以调用实例方法，例如 get_params
    strategy_cls = strategy_instance.get_params()

    # 也可以直接访问实例属性，例如 params
    print(strategy_instance.params)

    user_input_params = {}
   
    return user_input_params

    
def analyze_returns(symbol_returns, start_datetime:datetime,output_path:str):
    # Dictionary to store individual returns for each symbol
    symbol_individual_returns = {}
    log_file_path = os.path.join(output_path, f'_summary.log')
    
    
    with open(log_file_path, 'a') as f:
        #输出选择的参数
        f.write(f"起始时间: {start_datetime}")
        f.write('\n')
        for symbol, returns in symbol_returns.items():
            if isinstance(returns, Exception):
                print(f"Exception occurred for symbol {symbol.symbol}: {returns}")
                f.write(f"Exception occurred for symbol {symbol.symbol}: {returns}")
                f.write('\n')
                # Handle the exception as needed
            elif returns != cash:
                revenue = returns - cash
                symbol_individual_returns[symbol.symbol] = revenue

    # 对 symbol_individual_returns 字典按照值进行排序
    sorted_returns = sorted(symbol_individual_returns.items(), key=lambda x: x[1], reverse=True)
   
    symbols = ''
    with open(log_file_path, 'a') as f:
        print("\n每个Symbol的收益金额:")
        for symbol, individual_return in sorted_returns:
            symbols += f"{symbol} "
            content= f"{symbol}: {individual_return:.2f}"
            print(content)
            f.write(content)
            f.write('\n')
        f.write(symbols)
        f.write('\n')
                   
def select_strategy():
    for i, strategy in enumerate(all_strategies):
        strategy_name = getattr(strategy.params, 'name')
        print(f"{i + 1}.  {strategy_name}[{strategy.__name__}]")

    while True:
        user_input = input("请输入要运行的策略编号（输入exit结束选择）: ")
        if user_input.lower() == 'exit':
            break
        elif user_input.isdigit():
            index = int(user_input) - 1
            if 0 <= index < len(all_strategies):
                print(f"已选择运行策略: {all_strategies[index].__name__}")
                return all_strategies[index]

            else:
                print("无效的策略编号，请重新输入")
        else:
            print("无效的输入，请输入数字或exit")

def run_strategy(input_symbol, period, days, strategy_cls):
    if isinstance(strategy_cls, str):
        for i, strategy in enumerate(all_strategies):
            print(strategy.__name__, strategy_cls)
            if strategy.__name__ == strategy_cls:
                strategy_cls = strategy
                break
    output_path = os.path.join(current_working_directory, 'output', strategy_cls.params.name,  f'{period}-{datetime.now().strftime("%Y-%m-%d-%H-%M")}' )

    if not os.path.exists(output_path):
        # 不存在则创建
        os.makedirs(output_path)
    # database.global_init("edge.db")
 
    symbols = []
    # Get all symbols
    with database.create_database_session() as db_sess:
        if input_symbol:
            symbols = [get_by_symbol(db_sess, s, "US") for s in input_symbol.split(' ')]
        else:
            symbols = getAll(db_sess)   
      

    start_datetime = datetime.now() - timedelta(days=days)

    symbol_returns = {}
    
    symbols = [symbol for symbol in symbols if symbol is not None]


    with concurrent.futures.ThreadPoolExecutor(max_workers= 50) as executor:
        futures = [executor.submit(process_strategy, symbol, period, start_datetime, strategy_cls, output_path ) for symbol in symbols]

        for future in concurrent.futures.as_completed(futures):
            symbol, result_or_exception = future.result()

            if isinstance(result_or_exception, Exception):
                symbol_returns[symbol] = result_or_exception
            elif result_or_exception:
                symbol_returns[symbol] = result_or_exception  # Replace with the actual return value from your strategy

    # Analyze and display returns
    analyze_returns(symbol_returns, start_datetime, output_path)
    
if __name__ == '__main__':

    input_symbol = None
    input_symbol = input(f"请输入需要回测的证券代码以空格分割（默认为全部）: ") or input_symbol
    period = '1d'
    period = input(f"请输入K线数据类型（默认为 {period}）: ") or period

    default_days = 5
    default_days = input(f"请输入回测的天数（默认为 {default_days}）: ") or default_days

    days = int(default_days)

    strategy_cls = select_strategy()
 
    print(strategy_cls)
    
    run_strategy(input_symbol, period, days, strategy_cls)

   