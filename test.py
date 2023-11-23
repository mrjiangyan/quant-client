import easyquotation
quotation = easyquotation.use("hkquote")
Res_Sina_stocks = quotation.real(['AAPL','00700'], prefix= True)
print(Res_Sina_stocks)

# print(quotation.all_market)

# quotation = easyquotation.use('tencent')
# loaded_codes_list=quotation.load_stock_codes()    #返回无前缀的股票代码列表，也含有一些基金代码
# print(loaded_codes_list)