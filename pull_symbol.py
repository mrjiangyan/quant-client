import pandas as pd
from loguru import logger
from data.model.t_symbol import Symbol
import os
from data.service.symbol_service import get_by_symbol
from data import database

 # 必须要通过app上下文去启动数据库
database.global_init("edge.db")

url = "blob:https://www.nasdaq.com/a57045f7-ec5e-4f27-9502-0bf84d305728"

local_path = "nasdaq_screener_1701824629687.csv"

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
            if is_create == False:
                # 如果记录已经存在于数据库中，使用 merge 进行更新
                db_sess.merge(domain)
            else:
                db_sess.add(domain)
            db_sess.commit()