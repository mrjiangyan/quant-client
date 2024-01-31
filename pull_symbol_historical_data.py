import os
import time
from datetime import datetime, time
import resource
# 获取当前资源限制
soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
print(f"Current soft limit: {soft_limit}, hard limit: {hard_limit}")

# 设置文件描述符数量限制为无穷大
resource.setrlimit(resource.RLIMIT_NOFILE, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))

# 获取设置后的资源限制
soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
print(f"Updated soft limit: {soft_limit}, updated hard limit: {hard_limit}")
import concurrent.futures
from data.service.symbol_service import getAll, get_by_symbol
from data import database
from data.model.t_symbol import Symbol
import pandas as pd
from yahooquery import Ticker
from loguru import logger
import traceback
import argparse

# Limit the number of symbols to download concurrently
max_concurrent_downloads = 25

file_expire_seconds = 6 * 60 * 60 
index_col = 'Date'
interval_map = {"1d": 'max', '1m': '1d', '5m': '7d', '15m': '7d', '1wk': 'max', "1h": 'ytd', "60m": 'ytd' }
interval_map = { "1d": 'max' , '1m': '1d', "1h": 'ytd','1wk': 'max'}
interval_map = { "1d": 'max','1wk': 'max', '1m': '1d' }

# Function to download historical data for a symbol
def download_data(symbol:Symbol, root_path):
    symbol_code = symbol.symbol.replace(" ", "")
    print(symbol_code)
    for key, value in interval_map.items():
        try:
            directory_path =  os.path.join(root_path,  key)
            os.makedirs(directory_path, exist_ok=True)
            file_path = os.path.join(directory_path, f"{symbol_code}.csv")
            if should_download(symbol,file_path):
                download_yahoo(symbol, value, key, file_path)             
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Error downloading data for {symbol_code},{key}: {e}")
    

def download_yahoo(symbol:Symbol, period, interval, file_path):
    ticker = Ticker(symbol.symbol)
    df = ticker.history(period=period, interval=interval)
    if df.empty or 'date' not in df.index.names:
        logger.warning(f'{symbol.symbol},period:{period},interval:{interval} data is empty')
        return
    df.rename(columns={'close': 'Close', 'open': 'Open', 'volume': 'Volume', 'high': 'High', 'low': 'Low'}, inplace=True)
    df['Date'] = df.index.get_level_values('date')
    if 'adjclose' in df:
        columns_to_save =   ['Date','Open', 'High', 'Low', 'Close', 'adjclose', 'Volume']
    else:
        columns_to_save =   ['Date','Open', 'High', 'Low', 'Close', 'Volume']
    
    print(df)
    if interval not in ['1d', '1m', '1wk'] and os.path.exists(file_path):  
        existing_data = None
        existing_data = pd.read_csv(file_path, parse_dates=[index_col], index_col=index_col) 
        existing_data.index = pd.to_datetime(existing_data.index,  utc= True, errors='coerce')
        
        if isinstance(existing_data.index, pd.DatetimeIndex):
            existing_data.index = existing_data.index.tz_localize(None)  # Remove timezone if present
            existing_data.index = existing_data.index.tz_localize('UTC').tz_convert('Asia/Shanghai')
        elif pd.Timestamp(existing_data.index):
            existing_data.index = existing_data.index.tz_localize('UTC').tz_convert('Asia/Shanghai')
        else:
            print("Index type not recognized. Please check and handle accordingly.")
        df.reset_index(inplace=True)
        df = df[columns_to_save]
        df.set_index(index_col, inplace=True) 
    
        merged_data = pd.concat([existing_data, df])
        merged_data.index = pd.to_datetime(merged_data.index)

        # Sort the DataFrame by the index
        merged_data = merged_data.sort_index()
        merged_data = merged_data[~merged_data.index.duplicated(keep='last')]
       
        merged_data.reset_index().to_csv(file_path, index=False, columns=columns_to_save)

    else:
        if interval in ['1d', '1wk']:
            df['Date'] = pd.to_datetime(df[index_col], utc= True).dt.tz_convert('Asia/Shanghai').dt.strftime('%Y-%m-%d')
        if interval == '1m':
            df['Date'] = pd.to_datetime(df[index_col], utc= True).dt.tz_convert('Asia/Shanghai')
            # 使用 tail(1) 获取最后一行记录
            last_row = df.tail(1)

            # 通过列名获取 date 字段的日期部分的值
            last_date_str = last_row['Date'].dt.strftime('%Y-%m-%d').iloc[0]
            file_prefix, file_extension = os.path.splitext(file_path)
            # 构建新的文件名
            file_path = f"{file_prefix}_{last_date_str}{file_extension}"

        df.to_csv(file_path, index=False, columns=columns_to_save)

    
def should_download(symbol:Symbol, file_path:str):
    if '^' in symbol.symbol or '/' in symbol.symbol:
        return False
        
    # if symbol.last_price < 1 or symbol.last_price > 50:
    #     return False
     
    if is_night_time():
        return True
    if os.path.exists(file_path):
        # Get the file's last modification time
        last_modified_time = os.path.getmtime(file_path)
        # Get the current time
        current_time = datetime.now().timestamp()
        # Check if the file was modified in the last hour (3600 seconds)
        if current_time - last_modified_time < file_expire_seconds:
            return False
    return True

def is_night_time():
    # Get the current time
    current_time = datetime.now().time()

    # Define the start and end times for the night period
    night_start = time(21, 30)  # 9:30 PM
    night_end = time(5, 30)     # 5:30 AM

    # Check if the current time is between night_start and night_end
    return night_start <= current_time or current_time <= night_end



if __name__ == "__main__":
    database.global_init("edge.db")
    # Create the full path for the download file in the current directory
    download_path = os.path.join(os.getcwd(), 'resources','historical_data')
    # Create the directory if it doesn't exist
    os.makedirs(download_path, exist_ok=True)

    parser = argparse.ArgumentParser(description='Backtest trading strategies on historical data.')
    parser.add_argument('--symbol', nargs='+', help='指定的证券代码')
    
    args = parser.parse_args()
    symbols = []
    # Get all symbols
    with database.create_database_session() as db_sess:
        if args.symbol:
            symbols = [get_by_symbol(db_sess, s, "US") for s in args.symbol]
        else:
            symbols = getAll(db_sess)
      
    start_time = datetime.now()
    # Use ThreadPoolExecutor to download data concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers= max_concurrent_downloads) as executor:
        # Submit download tasks
        futures = [executor.submit(download_data, symbol, download_path) for symbol in symbols]

        # Wait for all tasks to complete
        concurrent.futures.wait(futures)


    end_time = datetime.now()

    total_time_seconds = (end_time - start_time).total_seconds()
    logger.info(f"All downloads completed. Total time: {total_time_seconds:.2f} seconds") 
