import pandas as pd
from loguru import logger
from data.model.t_symbol import Symbol
import os
from data.service.symbol_service import get_by_symbol
from data import database
import math
import time
from selenium import webdriver
from RPA.Browser.Selenium import Selenium
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
target_dir = os.getcwd()

browser = Selenium()
# Define Chrome options
chrome_options = webdriver.ChromeOptions()
# 页面加载策略
# chrome_options.page_load_strategy = 'normal'
# 启用无痕模式
# chrome_options.add_argument("--incognito")
# 其他配置选项（可选）
chrome_options.add_argument("--disable-extensions")
# 禁用软件光栅化器
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument('--allow-running-insecure-content')
# chrome_options.add_argument("blink-settings=imagesEnabled=false")
#彻底停用沙箱
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--ignore-certificate-errors")  
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation",'enable-logging'])
chrome_options.add_argument('--user-data-dir=C:\\seaco-rpa\\cache')
# chrome_options.add_argument('--user-data-dir=C:\\Users\\rpaadmin\\AppData\\Local\\Google\\Chrome\\User Data\\')

chrome_options.add_argument("--remote-debugging-port=9201")
# 以单进程模式运行 Chromium。（启动时浏览器会给出不安全警告）
chrome_options.add_argument("--single-process")
chrome_options.add_argument("--disable-web-security")
chrome_options.add_argument("--disable-gpu")
# chrome_options.add_argument("--disable-site-isolation-trials")

 # 窗体最大化
# windows系统写法
chrome_options.add_argument('start_maximized')
# mac系统写法
# chrome_options.add_argument('--start-fullscreen')
        
# 取消 请停用以开发者模式运行的扩展程序
chrome_options.add_experimental_option("useAutomationExtension", False)

chrome_options.add_experimental_option('prefs', {
    #是否禁止弹出窗口，默认为0
    'profile.default_content_settings.popups': 0,
    #是否使用自动下载
    "profile.default_content_setting_values.automatic_downloads": 2,
    'download.default_directory': target_dir,
    'download.prompt_for_download': False,
    'download.directory_upgrade': False,
    'safebrowsing.enabled': False,
    # 关掉密码弹窗
    "profile.password_manager_enabled": False,
    "credentials_enable_service": False
})

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
    
browser.set_selenium_implicit_wait(30)
xpath = f"xpath://button[@class='nasdaq-screener__form-button--download.ns-download-1']"
xpath = f"xpath://button[contains(@class,'nasdaq-screener__form-button--download.ns-download-1')]"
                        
browser.open_browser('https://www.nasdaq.com/market-activity/stocks/screener',  browser='chrome', options= chrome_options)
time.sleep(2)
print('浏览器打开成功')
buttons = browser.find_elements("//button")
print(buttons)
# 遍历找到的按钮元素
for button in buttons:
    # 执行你想要的操作，比如点击按钮
    class_name = button.get_attribute("class")
    if 'download' in class_name:
        print('搜索到按钮')
        driver = browser.driver
        actions = ActionChains(driver)  
        actions.move_to_element(button).perform()
        actions.click(button).perform()
        time.sleep(10)
        break

browser.close_browser()
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