import os
import time
from datetime import datetime, timedelta,time
from data.model.t_symbol import Symbol
import pandas as pd
from yahooquery import Ticker
from loguru import logger
import traceback
import argparse

# Limit the number of symbols to download concurrently
max_concurrent_downloads = 200

file_expire_seconds = 6 * 60 * 60 
index_col = 'Date'
interval_map = {"1d": 'max', '1m': '7d', '5m': '7d', '15m': '7d', '1wk': 'max', "1h": 'ytd', "60m": 'ytd' }
interval_map = { "1d": 'max' , '1m': '1d', "1h": 'ytd','1wk': 'max'}
# interval_map = { "1d": 'max' }


# Function to download historical data for a symbol
def download_data(symbol:Symbol, root_path):
    symbol_code = symbol.replace(" ", "")
    #print(symbol_code)
    for key, value in interval_map.items():
        try:
            directory_path =  os.path.join(root_path,  key)
            os.makedirs(directory_path, exist_ok=True)
            download_yahoo(symbol, value, key)             
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Error downloading data for {symbol_code},{key}: {e}")
    

def download_yahoo(symbol:Symbol, period, interval):
    ticker = Ticker(symbol)
    df = ticker.history(period=period, interval=interval)
    print(df)


def is_night_time():
    # Get the current time
    current_time = datetime.now().time()

    # Define the start and end times for the night period
    night_start = time(21, 30)  # 9:30 PM
    night_end = time(5, 30)     # 5:30 AM

    # Check if the current time is between night_start and night_end
    return night_start <= current_time or current_time <= night_end



if __name__ == "__main__":
   # Create the full path for the download file in the current directory
    download_path = os.path.join(os.getcwd(), 'historical_data')
      
    download_data('AAP', download_path)
