import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from datetime import datetime
import requests
import pandas as pd
import io

def fetch(ticker, start="2022-01-01", end="2022-02-02",intervalstr="1d"):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9'
    }
 
    url = "https://query1.finance.yahoo.com/v7/finance/download/" + str(ticker)
    x = int(datetime.strptime(start, '%Y-%m-%d').timestamp())
    y = int(datetime.strptime(end, '%Y-%m-%d').timestamp())
    url += "?period1=" + str(x) + "&period2=" + str(y) + "&interval="+intervalstr+"&events=history&includeAdjustedClose=true"
    print(url)
    r = requests.get(url, headers=headers,verify=False)
    
    pd1 = pd.read_csv(io.StringIO(r.text), index_col=0, parse_dates=True)
    print(r.text)
    return pd1
#使用AAPL测试
now =datetime.strptime('2022-05-30', '%Y-%m-%d')
print(int(now.timestamp()) )
startv = "2022-01-03"
endv = str( datetime.now().strftime("%Y-%m-%d"))
print(endv)
data = fetch("AAPL",start=startv,end=endv,intervalstr="1d")
