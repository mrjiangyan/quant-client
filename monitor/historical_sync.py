import os
import time
import concurrent.futures
from data.service.symbol_service import getAll
from data import database
from data.model.t_symbol import Symbol
import pandas as pd
from yahooquery import Ticker
from loguru import logger
from datetime import datetime,time

# Limit the number of symbols to download concurrently
max_concurrent_downloads = 200

file_expire_seconds = 6 * 3600

index_col = 'Date'
interval_map = {"1d": 'max', '1m': '7d', '5m': '7d', '15m': '7d', '1wk': 'max', "1h": 'ytd' }


# Function to download historical data for a symbol
def download_data(symbol:Symbol, root_path):
    symbol_code = symbol.symbol.replace(" ", "")
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
        df.to_csv(file_path, index=False, columns=columns_to_save)

    
    
def should_download(symbol:Symbol, file_path:str):
    if '^' in symbol.symbol or '/' in symbol.symbol:
        return False
         
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



def sync():
    # Create the full path for the download file in the current directory
    download_path = os.path.join(os.getcwd(), 'resources', 'historical_data')
    # Create the directory if it doesn't exist
    os.makedirs(download_path, exist_ok=True)

    symbols = []
    # Get all symbols
    with database.create_database_session() as db_sess:
        symbols = getAll(db_sess) 
    
    start_time = time()

    # Use ThreadPoolExecutor to download data concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers= max_concurrent_downloads) as executor:
        # Submit download tasks
        futures = [executor.submit(download_data, symbol, download_path) for symbol in symbols]

        # Wait for all tasks to complete
        concurrent.futures.wait(futures)

    end_time = time()

    total_time = end_time - start_time
    logger.info(f"All downloads completed. Total time: {total_time:.2f} seconds")
    
