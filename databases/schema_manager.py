from ELTReportFinance1.config.database_config import get_database_config

def create_mongodb_schema(db):
    collection = get_database_config()["mongodb"].collection
    db.drop_collection("report_finance")
    db.create_collection("report_finance", validator={
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id_group", "stock_code", "company_name"],
            "properties": {
                "id_group": {
                    "bsonType": "int"},
                "company_name": {
                    "bsonType": "string"},
                "stock_code": {
                    "bsonType": "string"},
                "year": {
                    "bsonType": ["int", "null"]},
                "quarter": {
                    "bsonType": ["int", "null"]},
                "report_type": {
                    "bsonType": ["string", "null"]},
                "file_format": {
                    "bsonType": ["string", "null"]},
                "file_name": {
                    "bsonType": ["string", "null"]},
                "source_url": {
                    "bsonType": ["string", "null"]},
                "local_path": {
                    "bsonType": ["string", "null"]},
                "minio_path": {
                    "bsonType": ["string", "null"]},
                "status_download" : {
                    "bsonType" : ["bool", "null"]},
                "status_uploaded": {
                    "bsonType": ["bool", "null"]},
                "status_extracted": {
                    "bsonType": ["bool", "null"]},
                "status_transformed": {
                    "bsonType": ["bool", "null"]},
                "created_at": {
                    "bsonType": ["date", "null"]},
                "updated_at": {
                    "bsonType": ["date", "null"]}
            }
        }
    })

    print(f"-----Created collection {collection} successfully------")

def validate_mongodb_schema(db):
    collection = db.list_collection_names()
    # print(f"------collection names: {collection} ----")
    if "report_finance" not in collection:
        raise ValueError("------collection doesn't exist----")

    #validate insert data into mongodb
    report_finance = db.report_finance.find_one({"stock_code": "ACB"})
    if not report_finance:
        raise ValueError("------stock_code ACB not found in mongodb----")

    print("----------Validated schema successfully-------")