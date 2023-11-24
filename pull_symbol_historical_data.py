import os
import time
import requests
import concurrent.futures
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from data.service.symbol_service import getAll
from data import database
from data.model.t_symbol import Symbol
import pandas as pd
from yahooquery import Ticker
from loguru import logger
import traceback

max_retries = 5
retry_delay = 5  # seconds
# Limit the number of symbols to download concurrently
max_concurrent_downloads = 5

interval_map = {"1d": 'max', '1m': '7d', '5m': '7d', '15m': '7d', '30m': '1mo', "1h": '6mo' }
# interval_map = { '1m': '7d' }
# Function to create a session with a connection pool
def create_session():
    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS"]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


# Function to download historical data for a symbol
def download_data(symbol:Symbol, root_path):
    symbol_code = symbol.symbol.replace(" ", "")
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
    

def download_1d(session, symbol_code, file_path):
    headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Cookie": "visitor-id=3437278853490150000V10; data-mn=3437278863490106000V10~~1; data-opx=a89cb73c-8eb3-48a9-9770-265531f9d712~~1; data-pub=35BE2056-0984-44DE-BA6B-AE30EA464B8B~~1; usp_status=1; data-zta=1991787319451354786~~63; data-gum=a_d00541f7-125b-469f-b65e-e0ed30ae7521~~63; data-crt=k-VRgzbl01CzWuWmvh4xaAIV3UnafZAyPOAqq74A~~63; data-mag=LPC1ZAU0-1I-2DUB~~63; data-ylm=3FVZGxxfZZxbwEH36nT3~~63; data-sht=1901683f-118b-43e4-b11a-cdb84ee7b9b5~~63",
            # 添加其他自定义的请求头...
    }
    url = f"https://query1.finance.yahoo.com/v7/finance/download/{symbol_code}?period1=1277769600&period2={int(time.time())}&interval=1d&events=history&includeAdjustedClose=true"

    for attempt in range(max_retries):
        try:
            response = session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            with open(file_path, "wb") as file:
                file.write(response.content)
                print(f"文件下载成功并保存为 {file_path}")
                break
        except requests.RequestException as e:
                print(f"Error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    # Sleep or add other logic for backoff before retrying
                    time.sleep(2)

def download_yahoo(symbol:Symbol, period, interval, file_path):
    ticker = Ticker(symbol.symbol, asynchronous=True, backoff_factor=1, max_workers=1, retry=5, timeout = 30)
    df = ticker.history(period=period, interval=interval)
    if df.empty or 'date' not in df.index.names:
        logger.warning(f'{symbol.symbol},period:{period},interval:{interval} data is empty')
        return
    df.rename(columns={'close': 'Close', 'open': 'Open', 'volume': 'Volume', 'high': 'High', 'low': 'Low'}, inplace=True)
    df['Date'] = df.index.get_level_values('date')
    columns_to_save = ['Date','Open', 'High', 'Low', 'Close', 'Volume']
    if os.path.isfile(file_path):     
        existing_data = pd.read_csv(file_path, parse_dates=['Date'], index_col='Date', infer_datetime_format=True)  
        existing_data.index = existing_data.index.tz_convert('America/New_York')
      
        df.reset_index(inplace=True)
        df = df[columns_to_save]
        df.set_index('Date', inplace=True) 
    
        merged_data = pd.concat([existing_data, df]).sort_values('Date')
        merged_data = merged_data[~merged_data.index.duplicated(keep='last')]
        logger.info(merged_data)
        merged_data.to_csv(file_path, index=False, columns=columns_to_save)

    else:
        df.to_csv(file_path, index=False, columns=columns_to_save)

    
    
def should_download(symbol:Symbol, file_path:str):
    if '^' in symbol.symbol or '/' in symbol.symbol:
        return False
         
    
    # if symbol.symbol.startswith('A') == False:
    #     print(symbol.symbol)
    #     return False
    # 如果价格小于10元则暂时不用下载
    if symbol.last_price < 10 or symbol.last_price > 2000:
        return False
    
    # 成交量小于50万股的也不需要
    if symbol.volume and symbol.volume < 50 * 1000:
            return False
        
        # 如果市值小于10元则暂时不用下载
    if symbol.market_cap is None or symbol.market_cap < 10000000:
        return False
    if os.path.exists(file_path):
        # Get the file's last modification time
        last_modified_time = os.path.getmtime(file_path)
        # Get the current time
        current_time = time.time()
        # Check if the file was modified in the last hour (3600 seconds)
        if current_time - last_modified_time < 7200:
            return True
        else:
            return True
    else:
        return True


def main():
    database.global_init("edge.db")
    # Create the full path for the download file in the current directory
    download_path = os.path.join(os.getcwd(), 'historical_data')
    # Create the directory if it doesn't exist
    os.makedirs(download_path, exist_ok=True)

    # Create a session with a connection pool
    session = create_session()

    symbols = []
    # Get all symbols
    with database.create_session() as db_sess:
        symbols = getAll(db_sess)
        
    
    # Use ThreadPoolExecutor to download data concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent_downloads) as executor:
        # Submit download tasks
        futures = [executor.submit(download_data, symbol, download_path, session) for symbol in symbols]

        # Wait for all tasks to complete
        concurrent.futures.wait(futures)

    logger.info("All downloads completed.")
    

if __name__ == "__main__":
    main()
