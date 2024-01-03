import pandas as pd
from loguru import logger
from data.model.t_symbol import Symbol
import os
from data.service.symbol_service import get_by_symbol
from data import database
import math
import tagui as t
import shutil
def find_recently_added_file(folder_path, prefix="nasdaq_", extension=".csv"):  
    files = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        # 检查文件名前缀、后缀和创建时间
        if filename.startswith(prefix) and filename.endswith(extension):
            files.append(file_path)

    # 根据文件创建时间从新到旧排序
    files.sort(key=lambda x: os.path.getctime(os.path.join(folder_path, x)), reverse=True)

    if files:
        return files[0]
    else:
        return None
    
t.init()
t.url('https://www.nasdaq.com/market-activity/stocks/screener')
t.click('.nasdaq-screener__form-button--download.ns-download-1')
t.wait()
t.close()
# 替换成你的文件夹路径
folder_path = os.getcwd()
filename = find_recently_added_file(folder_path)
print("最近新增的文件:", filename)
# Get the current working directory
current_directory = os.getcwd()

new_file_path = os.path.join(current_directory ,  'resources','screener',  "nasdaq_latest.csv")
shutil.move(filename, new_file_path)


 # 必须要通过app上下文去启动数据库
database.global_init("edge.db")

local_path = "nasdaq_latest.csv"

# Get the current working directory
current_directory = os.getcwd()

# Create the full path for the download file in the current directory
download_path = os.path.join(current_directory, 'resources', 'screener',local_path)

# Read CSV directly from the URL
tables = pd.read_csv(download_path)
logger.info(tables)

dataframes = []
# Append the DataFrame to the list
dataframes.append(tables)
with database.create_session() as db_sess:    
    for df in dataframes:
        # Loop through each row of the DataFrame
        for index, row in df.iterrows():
            symbol = str(row['Symbol']).upper()
            if any(char in symbol for char in '^/'):
                continue
            logger.info(symbol)
            is_create = False
            domain = get_by_symbol(db_sess, symbol,'US')
            if domain is None:
                domain = Symbol()
                domain.symbol = symbol
                is_create = True
            print(row)
            domain.country = row['Country'] 
            domain.industry = row['Industry'] 
            domain.ipo_year = row['IPO Year'] 
            domain.volume = row['Volume'] 
            domain.name = row['Name'] 
            domain.last_price = row['Last Sale'].replace("$","")
            domain.market = 'US'
            domain.market_cap = row['Market Cap']
            market_cap = float(domain.market_cap)
            if domain.market_cap is not None and not math.isnan(market_cap):
                domain.shares_outstanding = int(market_cap / float(domain.last_price))
            else:
                domain.shares_outstanding = 0
            if row['% Change']:
                domain.change = str(row['% Change']).replace('%','')
            if is_create == False:
                # 如果记录已经存在于数据库中，使用 merge 进行更新
                db_sess.merge(domain)
            else:
                db_sess.add(domain)
            db_sess.commit()