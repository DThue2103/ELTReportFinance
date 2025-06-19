
import requests
import pandas as pd
from bs4 import BeautifulSoup
import os
import re
from unidecode import unidecode


url = "https://topi.vn/danh-sach-ma-chung-khoan-theo-nganh-tai-viet-nam.html"

response = requests.get(url)

soup = BeautifulSoup(response.content, "html.parser")

h3s = soup.findAll("h3")

folder_path = r"/ELTReportFinance"
folder_stock_group = os.path.join(folder_path, "data")
os.makedirs(folder_stock_group, exist_ok=True)
data = []
for h3 in h3s:
    strong = h3.find("strong")
    if not strong:
        continue

    #lấy tên nhóm cổ
    nameStockGroup = strong.get_text(strip=True)
    nameStGr = unidecode(nameStockGroup).lower().replace("-", "")
    nameStGr = " ".join(nameStGr.split())
    group_id = int(nameStGr.split('.')[0])
    key1 = "nganh"
    key2 = "co phieu"
    name_df = ""
    # print(nameStGr)
    # print(group_id)
    if key1 in nameStGr:
        name_df = nameStGr.split(key1, 1)[1].strip().replace(" ", "")
        # print(name_df)
    if key1 not in nameStGr and key2 in nameStGr:
        name_df = nameStGr.split(key2, 1)[1].strip().replace(" ", "")
        # print(name_df)

    tables = h3.find_next("table")

    for i, table in enumerate(tables):
        if not table:
            continue

        rows = table.find_all("tr")

        if not rows or len(rows) < 2:
            continue

        for row in rows[1:]:
            cols = row.find_all("td")
            row_data = [col.get_text(strip=True) for col in cols]
            if row_data:
                row_data = [group_id] + row_data
                data.append(row_data)


df = pd.DataFrame(data, columns=["id_group", "company_name", "stock_code"])
print(df)

# #loại bỏ các mã trùng lặp
# df = df.drop_duplicates(subset=['stock_code'])
# print(df)

csv_path = os.path.join(folder_stock_group,f"macophieu.csv")
df.to_csv(csv_path, index=False, encoding='utf-8-sig')
