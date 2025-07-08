import json
import requests
from bs4 import BeautifulSoup
import os
from unidecode import unidecode


url = "https://topi.vn/danh-sach-ma-chung-khoan-theo-nganh-tai-viet-nam.html"

response = requests.get(url)

soup = BeautifulSoup(response.content, "html.parser")

h3s = soup.find_all("h3")

folder_path = r"/ELTReportFinance1"
folder_stock_group = os.path.join(folder_path, "data")
os.makedirs(folder_stock_group, exist_ok=True)
stock_info = []
group_stock = []
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
        name_df = nameStGr.split(key1, 1)[1].strip().replace(" ", "_")
        # print(name_df)
    if key1 not in nameStGr and key2 in nameStGr:
        name_df = nameStGr.split(key2, 1)[1].strip().replace(" ", "_")
        # print(name_df)
    group_stock.append({
        "id_group": group_id,
        "stock_group_name": name_df
    })
    tables = h3.find_next("table")

    for i, table in enumerate(tables):
        if not table:
            continue

        rows = table.find_all("tr")

        if not rows or len(rows) < 2:
            continue

        for row in rows[1:]:
            cols = row.find_all("td")
            # row_data = [col.get_text(strip=True) for col in cols]
            company_name = cols[0].get_text(strip=True)
            stock_code = cols[1].get_text(strip=True)
            stock_info.append({
                "id_group": group_id,
                "company_name": company_name,
                "stock_code": stock_code
            })

not_duplicate_stock_code = set()
unique_stock_code_json = []
for item in stock_info:
    if item["stock_code"] not in not_duplicate_stock_code:
        unique_stock_code_json.append(item)
        not_duplicate_stock_code.add(item["stock_code"])

group_stock_path = os.path.join(folder_stock_group,f"group_stock_code.json")
stock_info_path = os.path.join(folder_stock_group,f"stock_info.json")
with open(group_stock_path, "w", encoding="utf-8") as f:
    json.dump(group_stock, f, ensure_ascii=False, indent=4)
    print("----write group_stock to json file successfully----")

with open(stock_info_path, "w", encoding="utf-8") as f:
    json.dump(unique_stock_code_json, f, ensure_ascii=False, indent=4)
    print("----write stock_info to json file successfully----")
