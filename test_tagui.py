import tagui as t
from bs4 import BeautifulSoup

t.init()
t.url('http://daip-test.ai-prime.com:8003/home')

t.wait()
print(t.url())
# 如果是没有登录状态
if 'login' in t.url():
    t.click('form_item_account')
    t.type('form_item_account', 'sysAdmin')
    t.click('form_item_password')
    t.type('form_item_password', '1234qwer  ')
    t.click("//button[@type='button' and contains(@class, 'ant-btn ant-btn-lg')]")

x_path = "//section[contains(.//text(),'视频监管系统')]"
print(t.check(t.read(x_path), '存在视频监管系统', '不存在视频监管系统'))
t.click(x_path)

x_path = "//span[contains(.//text(),'历史记录')]"
print(t.check(t.read(x_path), '存在历史记录菜单项', '不存在历史记录菜单项'))
t.click(x_path)
x_path = "//span[contains(.//text(),'报警记录')]"
print(t.check(t.read(x_path), '存在报警记录菜单项', '不存在报警记录菜单项'))
t.click(x_path)

t.type('form_item_baojing_mingcheng', '[clear]未佩戴安全帽')
t.type('form_item_baojing_dengji', '[clear]一般')
x_path = "//span[contains(.//text(),'查询')]"
if not t.present(x_path):
    print('不存在查询按钮')
    exit()
t.click(x_path)

x_path = "//table"
html_content = t.read('page')
#print(html_content)

if '报警名称' in html_content:
    print('搜索到报警名称')
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table')
    # Print the table (or perform other operations)
    print(table)

# t.close()