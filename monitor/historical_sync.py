import os
import time
import concurrent.futures
from data.service.symbol_service import getAll
from data import database
from data.model.t_symbol import Symbol
import pandas as pd
from yahooquery import Ticker
from loguru import logger
import traceback

# Limit the number of symbols to download concurrently
max_concurrent_downloads = 25

file_expire_seconds = 3 * 3600

index_col = 'Date'
interval_map = {"1d": 'max', '1m': '7d', '5m': '7d', '15m': '7d', '30m': '1mo', "1h": 'ytd', "60m": 'ytd' }


# Function to download historical data for a symbol
def download_data(symbol:Symbol, root_path):
    symbol_code = symbol.symbol.replace(" ", "")
    print(symbol_code)
    for key, value in interval_map.items():
        try:
            directory_path =  os.path.join(root_path,  key)
            os.makedirs(directory_path, exist_ok=True)
            file_path = os.path.join(directory_path, f"{symbol_code}.csv")
            if should_download(symbol, file_path):
                download_yahoo(symbol, value, key, file_path)             
        except Exception as e:
            # traceback.print_exc()
            logger.error(f"Error downloading data for {symbol_code},{key}: {e}")
    
def download_yahoo(symbol:Symbol, period, interval, file_path):
    ticker = Ticker(symbol.symbol, asynchronous=True)
    df = ticker.history(period=period, interval=interval)
    if df.empty or 'date' not in df.index.names:
        logger.warning(f'{symbol.symbol},period:{period},interval:{interval} data is empty')
        return
    df.rename(columns={'close': 'Close', 'open': 'Open', 'volume': 'Volume', 'high': 'High', 'low': 'Low'}, inplace=True)
    df[index_col] = df.index.get_level_values('date')
    if 'adjclose' in df:
        columns_to_save =   ['Date','Open', 'High', 'Low', 'Close', 'adjclose', 'Volume']
    else:
        columns_to_save =   ['Date','Open', 'High', 'Low', 'Close', 'Volume']
    # print(df)
    if interval != '1d' and  interval != '1m'  and os.path.isfile(file_path):     
        existing_data = None
        existing_data = pd.read_csv(file_path, parse_dates=[index_col], index_col=index_col) 
        existing_data.index = pd.to_datetime(existing_data.index,  utc= True, errors='coerce')
       
        if isinstance(existing_data.index, pd.DatetimeIndex):
            existing_data.index = existing_data.index.tz_localize(None)  # Remove timezone if present
            existing_data.index = existing_data.index.tz_localize('UTC').tz_convert('America/New_York')
        elif pd.Timestamp(existing_data.index):
            existing_data.index = existing_data.index.tz_localize('UTC').tz_convert('America/New_York')
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
        if interval == '1d':
            df[index_col] = pd.to_datetime(df.index.get_level_values('date')).tz_localize('UTC')
            # Convert to a string
            df[index_col] = df[index_col].dt.strftime('%Y-%m-%d')
        df.to_csv(file_path, index=False, columns=columns_to_save)

    
    
def should_download(symbol:Symbol, file_path:str):
    if '^' in symbol.symbol or '/' in symbol.symbol:
        return False
         
    download = True
    if symbol.last_price < 1:
        download = False
    # 如果市值小于10元则暂时不用下载
    if symbol.market_cap is None or symbol.market_cap < 500 * 10000:
        download = False
    # 如果文件已经存在则忽略上述的条件 无论如何都会根据文件修改时间的处理逻辑做判断
    if os.path.exists(file_path):
        # Get the file's last modification time
        last_modified_time = os.path.getmtime(file_path)
        # Get the current time
        current_time = time.time()
        # Check if the file was modified in the last hour (3600 seconds)
        if current_time - last_modified_time < file_expire_seconds:
            return False
        else:
            return True
    else:
        return download and True


def sync():
    # Create the full path for the download file in the current directory
    download_path = os.path.join(os.getcwd(), 'historical_data')
    # Create the directory if it doesn't exist
    os.makedirs(download_path, exist_ok=True)

    symbols = []
    # Get all symbols
    with database.create_session() as db_sess:
        symbols = getAll(db_sess)
        
    
    # Use ThreadPoolExecutor to download data concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers= max_concurrent_downloads) as executor:
        # Submit download tasks
        futures = [executor.submit(download_data, symbol, download_path) for symbol in symbols]

        # Wait for all tasks to complete
        concurrent.futures.wait(futures)

    logger.info("All downloads completed.")
    
