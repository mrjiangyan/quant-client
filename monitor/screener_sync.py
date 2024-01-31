import pandas as pd
from loguru import logger
from data.model.t_symbol import Symbol
import os
from data.service.symbol_service import get_by_symbol
from data import database
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import shutil
import os

local_path = "nasdaq_latest.csv"

# Get the current working directory
current_directory = os.getcwd()

# Create the full path for the download file in the current directory
download_path = os.path.join(current_directory, 'resources', 'screener', local_path)

last_success_date = None

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


def download(): 
    # 设置浏览器驱动路径
    driver_path = "/Users/jiangyan/Downloads/chromedriver"  # 替换成你的浏览器驱动路径
    # 创建ChromeDriver服务
    chrome_service = ChromeService(executable_path=driver_path)

    # 初始化Chrome浏览器
    browser = webdriver.Chrome(service=chrome_service)
    # 打开指定网页
    url = "https://www.nasdaq.com/market-activity/stocks/screener"
    browser.get(url)

    # 等待直到指定区域（按钮）可见
    wait = WebDriverWait(browser, 30)
    element = wait.until(EC.visibility_of_element_located((By.XPATH, "//button[@class='nasdaq-screener__form-button--download ns-download-1']")))

    # 滚动到按钮所在位置，将元素移动到屏幕中央
    browser.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element)

    # 定位并点击指定区域（示例中使用XPath）
    element.click()

    # 等待下载完成（示例中使用10秒的等待时间，可以根据实际情况调整）
    #wait.until(EC.invisibility_of_element_located((By.XPATH, "//button[@class='nasdaq-screener__form-button--download ns-download-1']")))
    wait = WebDriverWait(browser, 30)

    # 关闭浏览器
    browser.quit()

    # 替换成你的文件夹路径
    folder_path = "/Users/jiangyan/Downloads/"
    filename = find_recently_added_file(folder_path)
    print("最近新增的文件:", filename)
   
    new_file_path = os.path.join(current_directory ,  'resources','screener',  "nasdaq_latest.csv")
    shutil.move(filename, new_file_path)



def sync():
    if os.path.exists(local_path) == False:
        return
    current_date = datetime.now().strftime("%Y%m%d")
    if last_success_date == current_date:
        return
    # Read CSV directly from the URL
    tables = pd.read_csv(download_path)

    dataframes = []
    # Append the DataFrame to the list
    dataframes.append(tables)
    with database.create_database_session() as db_sess:    
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
    
    last_success_date = current_date