import ast
import json

from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error
import os
import pandas as pd
load_dotenv()
client = Minio(
    os.getenv("URL"),
    os.getenv("ACCESS_KEY"),
    os.getenv("SECRET_ACCESS_KEY"),
    secure=False  # MinIO local không dùng HTTPS
)
minio_url = os.getenv("URL")
# Tên bucket
bucket_name = "financial-reports"
records_finance_path = "/ELTReportFinance1/data/record_finance_report.json"
with open (records_finance_path, "r", encoding="utf-8") as f:
    records_finance = json.load(f)

for item in records_finance:
    file_path =  item["local_path"]
    if isinstance(file_path, str) and os.path.exists(file_path):
        st = os.stat(file_path)
        object_name = ""
        if os.path.isfile(file_path):
            object_name = file_path.split("/")[-1]  # lấy tên file

        content_type = object_name.split(".")[-1]  # lấy định dạng file
        # Upload
        try:
            client.fput_object(
                bucket_name, object_name, file_path,
                content_type=f"application/{content_type}"
            )
            # records_finance_df = records_finance_df.astype({"minio_path": "string"})
            # records_finance_df.loc[index, "minio_path"] = f"http://{minio_url}/{bucket_name}/{object_name}"
            # status_dict = ast.literal_eval(row["status"])  # lấy ra dict hiện tại
            # status_dict["uploaded"] = True  # cập nhật dict
            # records_finance_df.at[index, "status"] = status_dict  # gán lại dict vào DataFrame

            item["minio_path"] = f"http://{minio_url}/{bucket_name}/{object_name}"
            item["status"]["uploaded"] = True
            print(f"------Upload {object_name} to {bucket_name} successfully----")
        except S3Error as e:
            print(f"----Error when upload: {e}-----")
    else:
        print(f"------Path is not valid or not exist-----")

root_path = r"/ELTReportFinance1/data"
result_name = "uploaded_record_finance_report.json"
result_path = os.path.join(root_path, result_name)
with open (result_path, "w", encoding="utf-8") as f:
    json.dump(records_finance, f, ensure_ascii=False, indent=4)

print("----- Save uploaded metadata of records successfully-----")