from ELTReportFinance.config.mongodb_config import get_database_config
from ELTReportFinance.databases.mongodb_connect import MongoDBConnect
from ELTReportFinance.databases.schema_manager import create_mongodb_schema, validate_mongodb_schema
def main(config):
    with MongoDBConnect(config["mongodb"].uri, config["mongodb"].db_name) as mongodb_client:
        create_mongodb_schema(mongodb_client.connect())
        mongodb_client.db.report_finance.insert_one({
            "stock_code": "ACB",
            "company_name": "Ngân hàng á châu"
        })
        print("-----insert one document to mongodb----")
        validate_mongodb_schema(mongodb_client.connect())

if __name__ == '__main__':
    config = get_database_config()
    # print(config)
    main(config)