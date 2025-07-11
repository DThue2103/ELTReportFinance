from typing import List, Dict
from datetime import datetime
import requests
import pandas as pd
from time import sleep

from pandas import DataFrame
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import os
import re
import json
from unidecode import unidecode


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def truncate_to_milliseconds(dt: datetime) -> datetime:
    now = datetime.utcnow()
    return now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # bỏ 3 chữ số micro giây


def get_report_pdf_link(reportCode : str) -> List:
    """
    Hàm lấy link của các bctc để crawl
    :param reportCode: mã bctc
    :return: list các dict{"quarter", "year", "report_type", "source_url"}
    """
    # truy cập vào trang web thông tin trên cafef của từng công ty
    url = f"https://cafef.vn/du-lieu/hose/{reportCode}.chn"
    # print(url)

    chrome_options = Options()
    chrome_options.add_argument("--headless")

    # 1. Tạo service object, trỏ đến đường dẫn chromedriver
    driver_path = ChromeDriverManager().install()
    service = Service(driver_path)

    # 2. Khởi tạo trình duyệt
    browser = webdriver.Chrome(service=service, options=chrome_options)

    # 3. Mở trang web
    browser.get(url)

    # Kiểm tra xem có nút "Tải BCTC" hay không và nhấn vào
    try:
        wait = WebDriverWait(browser, 20)
        wait.until(EC.presence_of_element_located((By.ID, "lsTab5CT")))
        wait.until(EC.visibility_of_element_located((By.ID, "lsTab5CT")))
        button = wait.until(EC.element_to_be_clickable((By.ID, "lsTab5CT")))
        browser.execute_script("arguments[0].click();", button)
        # button.click()
        print(f"Đã click vào nút Tải BCTC của {reportCode}")
        sleep(5)
    except NoSuchElementException:
        print(f"[Lỗi] Không tìm thấy nút 'Tải BCTC' trên {url}.")
    except ElementClickInterceptedException:
        print(f"[Lỗi] Không thể click vào nút trên {url} - Có thể bị che khuất hoặc không tương tác được.")
    except Exception as e:
        print(f"[Lỗi khác] Xảy ra lỗi: {e} trên {url}")

    # Tìm thẻ chứa link báo cáo tài chính
    tables = browser.find_elements(By.CSS_SELECTOR, "table")
    reports = []
    target_table = None
    for table in tables:
        try:
            first_row = table.find_element(By.TAG_NAME, "tr")
            first_cell = first_row.find_element(By.TAG_NAME, "td")  # hoặc th
            cell_text = first_cell.text.strip().lower()

            if "loại báo cáo" in cell_text:
                target_table = table
                break  # chỉ lấy bảng đầu tiên phù hợp
        except:
            continue

    if target_table:
        rows = target_table.find_elements(By.TAG_NAME, "tr")
        for row in rows:
            report = {}
            tds = row.find_elements(By.TAG_NAME, "td")
            try:
                name_report = tds[0].text.strip().lower()
                name_report = unidecode(name_report)  # Bỏ dấu tiếng Việt
                name_report = re.sub(r"[^a-zA-Z0-9\s]", "", name_report)  # Bỏ ký tự đặc biệt
                # print(name_report)
                quarter_match = re.search(r"quy\s*(\d+)", name_report)
                if quarter_match:
                    report["quarter"] = int(quarter_match.group(1))
                else:
                    report["quarter"] = 0
                # Lấy năm
                year_match = re.search(r"nam\s*(\d{4})", name_report)
                if year_match:
                    report["year"] = int(year_match.group(1))

                #lấy loại báo cáo
                if "me" in name_report:
                    report["report_type"] = "CongTyMe"
                else:
                    report["report_type"] = "HopNhat"

                link_report = tds[2].find_element(By.TAG_NAME, "a").get_attribute("href")
                report["source_url"] = link_report
                # print("Tìm thấy link:", link_report)
                # print(report)
                reports.append(report)
                image_type_report = tds[2].find_element(By.TAG_NAME, "img").get_attribute("src")
                print(image_type_report)
                #lấy file format
                file_format = None
                if "rar" in image_type_report:
                    file_format = "rar"
                elif "pdf" in image_type_report:
                    file_format = "pdf"
                elif "zip" in image_type_report:
                    file_format = "zip"
                elif "word" in image_type_report:
                    file_format = "docx"
                elif "xls" in image_type_report:
                    file_format = "xlsx"

                report["file_format"] = file_format
            except:
                print("Không tìm thấy thẻ <a> trong ô thứ 3.")
    else:
        print("Không tìm thấy bảng chứa 'Loại báo cáo'")
    print(reports)
    browser.quit()
    return reports

#hàm tải file bctc pdf từ link vừa lấy
def download_report(reportCode : str, report_type : str, quarter : int, year: int, file_format : str, link_pdf : str, pdf_path : str) -> Dict:
    """
    hàm download bctc từ link web rồi lưu vào folder đích
    :param reportCode: mã bctc
    :param link_pdf: link dẫn tới web của pdf bctc
    :param pdf_path: path của folder lưu trữ file bctc
    :return file_name
    """
    if quarter != 0:
        file_name = f"{reportCode}_{report_type}_Q{quarter}_{year}.{file_format}"
    else:
        file_name = f"{reportCode}_{report_type}_{year}.{file_format}"
    file_path = os.path.join(pdf_path, file_name)
    response = requests.get(link_pdf)
    if response.status_code == 200:
        with open(file_path, "wb") as f:
            f.write(response.content)
            print(f"Tải thành công: {file_name}")
    else:
        print(f"Lỗi khi tải file, mã trạng thái: {response.status_code}")

    return {
        "file_name" : file_name,
        "local_path" : file_path
        # "local_path" : f"{pdf_path}\{file_path}"
    }

def crawlReport(folder_path : str, json_path: str) -> DataFrame:
    """
    Hàm crawl là tổng hợp các bước: tìm link bctc, download các bctc từ link
    sau đó lưu meta data của các pdf thành 1 file csv
    :param folder_path: folder để lưu trữ các file pdf crawl được
    :param json_path: path của file stock_infor.json chứa mã ngành, tên công ty, mã chứng khoán
    """
    pdf_path = os.path.join(folder_path, "pdfs")  # tạo folder ReportFinance để
    os.makedirs(pdf_path, exist_ok=True)
    # lấy link pdf từ browser
    records = []
    with open(json_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    for item in data:
        reportCode = item["stock_code"]
        reports = get_report_pdf_link(reportCode)
        print(reports)
        dict_field = {}
        if not reports:
            records.append({
                "id_group": item["id_group"],
                "company_name": item["company_name"],
                "stock_code": reportCode,
                "year": None,
                "quarter": None,
                "report_type": None,
                "file_format": None,
                "file_name": None,
                "source_url": None,
                "local_path": None,
                "minio_path": None,
                "status": {
                    "download": False,
                    "uploaded": False,
                    "extracted": False,
                    "transformed": False
                },
                "created_at": truncate_to_milliseconds(datetime.utcnow()),
                "updated_at": truncate_to_milliseconds(datetime.utcnow())
            })
        # dict_field["id_group"] = row.iloc[0]
        # dict_field["company_name"] = row.iloc[1]
        # dict_field["stock_code"] = reportCode
        # dict_field["status"] = {}
        for report in reports:
            link_pdf = report["source_url"]
            report_type = report["report_type"]
            quarter = report["quarter"]
            year = report["year"]
            file_format = report["file_format"]
            print(link_pdf)

            dict_field = {
                "id_group": item["id_group"],
                "company_name": item["company_name"],
                "stock_code": reportCode,
                "year": year,
                "quarter": quarter,
                "report_type": report_type,
                "file_format": file_format,
                "file_name": None,
                "source_url": link_pdf,
                "local_path": None,
                "minio_path": None,
                "status": {
                    "download": False,
                    "uploaded": False,
                    "extracted": False,
                    "transformed": False
                },
                "created_at": truncate_to_milliseconds(datetime.utcnow()),
                "updated_at": truncate_to_milliseconds(datetime.utcnow())
            }
            if link_pdf:
                download = download_report(reportCode, report_type, quarter, year, file_format, link_pdf, pdf_path)
                dict_field["file_name"] = download["file_name"]
                dict_field["source_url"] = link_pdf
                dict_field["local_path"] = download["local_path"]
                dict_field["status"]["download"] = True

            print(dict_field)
            records.append(dict_field)

    # result_df = pd.DataFrame(records)
    # print(result_df)
    # print(result_df.count())
    root_path = r"/home/huedt/Documents/PythonProjects/ELTReportFinance/data"
    result_name = "record_finance_report.json"
    result_path = os.path.join(root_path, result_name)
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(records, f, cls=DateTimeEncoder, ensure_ascii=False, indent=4)
        print("-----saved metadata of records successfully---")

    return records

if __name__ == '__main__':
    folder_path = r"/home/huedt/Documents/PythonProjects/ELTReportFinance"
    json_path = r"/home/huedt/Documents/PythonProjects/ELTReportFinance/data/test.json"
    crawlReport(folder_path, json_path)


