import pandas as pd
from loguru import logger
from data.model.t_symbol import Symbol
import os
from data.service.symbol_service import get_by_symbol
from data import database
import math


target_dir = os.getcwd()
# Get the current working directory
current_directory = os.getcwd()

# 必须要通过app上下文去启动数据库
database.global_init()

local_path = "nasdaq_latest.csv"

# Get the current working directory
current_directory = os.getcwd()

# Create the full path for the download file in the current directory
download_path = os.path.join(current_directory, 'resources', 'screener', local_path)

# Read CSV directly from the URL
tables = pd.read_csv(download_path)
logger.info(tables)

dataframes = []
# Append the DataFrame to the list
dataframes.append(tables)

with database.create_database_session() as db_sess:
    for df in dataframes:
        # Loop through each row of the DataFrame
        for index, row in df.iterrows():
            row = row.fillna('')  # 替换NaN值
            symbol = str(row['Symbol']).upper()
            if any(char in symbol for char in '^/'):
                continue
            logger.info(symbol)
            is_create = False
            domain = get_by_symbol(db_sess, symbol, 'US')
            if domain is None:
                domain = Symbol()
                domain.symbol = symbol
                domain.short = 1
                is_create = True
            print(row)
            if domain.country != row['Country'] and not row['Country']:
                domain.country = row['Country']
            domain.industry = row['Industry']
            domain.ipo_year = row['IPO Year']
            domain.volume = row['Volume'] 
            domain.name = row['Name'] 
            domain.last_price = row['Last Sale'].replace("$","")
            domain.market = 'US'
            domain.market_cap = row['Market Cap']
            market_cap = float(domain.market_cap)
            # 检查 domain.market_cap 是否为有效数值
            if isinstance(domain.market_cap, str):
                market_cap_str = domain.market_cap.strip()
                if market_cap_str != '':
                    try:
                        market_cap = float(market_cap_str)
                        domain.shares_outstanding = int(market_cap / float(domain.last_price))
                    except ValueError:
                        domain.shares_outstanding = 0  # 如果转换失败，设置 shares_outstanding 为 0
                else:
                    domain.shares_outstanding = 0  # 如果 market_cap 是空字符串，设置 shares_outstanding 为 0
            elif isinstance(domain.market_cap, (int, float)):
                market_cap = float(domain.market_cap)
                domain.shares_outstanding = int(market_cap / float(domain.last_price))
            else:
                domain.shares_outstanding = 0  # 如果 market_cap 不是有效数值，设置 shares_outstanding 为 0
            if row['% Change']:
                domain.change = str(row['% Change']).replace('%','')
            if is_create == False:
                # 如果记录已经存在于数据库中，使用 merge 进行更新
                db_sess.merge(domain)
            else:
                db_sess.add(domain)
            db_sess.commit()