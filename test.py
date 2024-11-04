import requests

url = "https://data.alpaca.markets/v1beta1/options/trades/latest?feed=indicative&symbols=NIO241108P00008000"
url = "https://data.alpaca.markets/v1beta1/options/snapshots/QQQ?feed=indicative&limit=100"

headers = {
    "accept": "application/json",
    "APCA-API-KEY-ID": "AK6N50RSOQD7KVA3YL1U",
    "APCA-API-SECRET-KEY": "qPJGf0Apx0Imsvgu9GpQxgEdip6JFnoQeq0njmxC"
}

response = requests.get(url, headers=headers)

# print(response.text)

from alpaca.data.historical import OptionHistoricalDataClient
from alpaca.data.requests import OptionChainRequest
from alpaca.data.enums import OptionsFeed
from alpaca.trading.enums import ContractType
from datetime import datetime

client = OptionHistoricalDataClient(api_key='AK6N50RSOQD7KVA3YL1U', secret_key='qPJGf0Apx0Imsvgu9GpQxgEdip6JFnoQeq0njmxC')
request_params = OptionChainRequest(
                        underlying_symbol="QQQ",
                        type=ContractType.PUT,
                        feed=OptionsFeed.INDICATIVE,
                        expiration_date='2024-11-04',
                        strike_price_lte='488',
                        strike_price_gte='488'
                        )

# print(client.get_option_chain())
row_data = client.get_option_chain(request_params)

# convert to dataframe
print(row_data)