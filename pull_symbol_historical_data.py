import yahooquery as yq
import pandas as pd
import yfinance as yf
from loguru import logger
from data.model.t_symbol import Symbol
import os
from data.service.symbol_service import getAll
from data import database
import requests
import time
from requests.exceptions import SSLError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

max_retries = 5
retry_delay = 5  # seconds


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


 # 必须要通过app上下文去启动数据库
database.global_init("edge.db")

# Get the current working directory
current_directory = os.getcwd()

session = create_session()

def should_download(file_path):
    # Check if the file exists
    if os.path.exists(file_path):
        # Get the file's last modification time
        last_modified_time = os.path.getmtime(file_path)

        # Get the current time
        current_time = time.time()

        # Check if the file was modified in the last hour (3600 seconds)
        if current_time - last_modified_time < 7200:
            print(f"The file {file_path} was modified within the last hour. Skipping download.")
            return False
        else:
            print(f"The file {file_path} is older than one hour. Proceeding with download.")
            return True
    else:
        print(f"The file {file_path} does not exist. Proceeding with download.")
        return True
    
# Create the full path for the download file in the current directory
download_path = os.path.join(current_directory, 'historical_data' , '1d')
# Create the directory if it doesn't exist
os.makedirs(download_path, exist_ok=True)

with database.create_session() as db_sess:    
    for symbol in getAll(db_sess):
        symbol_code = symbol.symbol.replace(" ", "")
        if '^' in symbol.symbol or '/' in symbol.symbol:
            continue
        file_path = download_path + f"/{symbol_code}.csv"
           
        # 如果价格小于10元则暂时不用下载
        if symbol.last_price < 10 or symbol.last_price > 2000:
            continue
        
        # 如果市值小于10元则暂时不用下载
        if symbol.market_cap is None or symbol.market_cap < 10000000:
            continue
        # 判断文件的创建时间, 如果文件存在并且最后更新时间在1个小时以内则不再重新下载
        if should_download(file_path) == False:
            continue
        #https://query1.finance.yahoo.com/v7/finance/download/TSLA?period1=1277769600&period2=1700697600&interval=1d&events=history&includeAdjustedClose=true
        #从yahoo下载历史日线的csv数据
        
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Cookie": "A3=d=AQABBH2LomMCEBbe93aF_dqN-HgXRP4TJXMFEgEBAQHco2OsYwAAAAAA_eMAAA&S=AQAAArej6YmGL_ivXQFMycfsbRQ; A1=d=AQABBH2LomMCEBbe93aF_dqN-HgXRP4TJXMFEgEBAQHco2OsYwAAAAAA_eMAAA&S=AQAAArej6YmGL_ivXQFMycfsbRQ; A1S=d=AQABBH2LomMCEBbe93aF_dqN-HgXRP4TJXMFEgEBAQHco2OsYwAAAAAA_eMAAA&S=AQAAArej6YmGL_ivXQFMycfsbRQ",
            # 添加其他自定义的请求头...
        }
        url = f"https://query1.finance.yahoo.com/v7/finance/download/{symbol_code}?period1=1277769600&period2={int(time.time())}&interval=1d&events=history&includeAdjustedClose=true"

        print(url)
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
     
