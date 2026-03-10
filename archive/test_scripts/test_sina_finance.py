import requests
import time

headers = {'Referer': 'https://finance.sina.com.cn'}

# 测试股票API
stock_url = "https://hq.sinajs.cn/list=sh000001"
# 测试新闻API
news_url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&num=5&page=1"

print("=== 股票数据测试 ===")
r = requests.get(stock_url, headers=headers)
print(f"状态码: {r.status_code}")
print(f"数据: {r.text[:100]}...")

print("\n=== 财经新闻测试 ===")
r = requests.get(news_url, headers=headers)
print(f"状态码: {r.status_code}")
data = r.json()
print(f"新闻总数: {data['result']['total']}")
print(f"本次返回: {len(data['result']['data'])} 条")
print(f"\n第一条新闻:")
print(f"标题: {data['result']['data'][0]['title']}")
print(f"链接: {data['result']['data'][0]['url']}")

print("\n=== 连续请求测试 (50次) ===")
success = 0
for i in range(50):
    r = requests.get(stock_url, headers=headers)
    if r.status_code == 200:
        success += 1
    time.sleep(0.1)
print(f"成功: {success}/50")
