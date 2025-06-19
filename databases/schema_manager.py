from ELTReportFinance.config.mongodb_config import get_database_config

def create_mongodb_schema(db):
    collection = get_database_config()["mongodb"].collection
    db.drop_collection("report_finance")
    db.create_collection("report_finance", validator={
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["stock_code", "company_name"],
            "properties": {
                "stock_code": {
                    "bsonType": "string"},
                "company_name": {
                    "bsonType": "string"},
                "year": {
                    "bsonType": ["int", "null"]},
                "quarter": {
                    "bsonType": ["int", "null"]},
                "stock_group": {
                    "bsonType": ["string", "null"]},
                "report_type": {
                    "bsonType": ["string", "null"]},
                "file_name": {
                    "bsonType": ["string", "null"]},
                "minio_path": {
                    "bsonType": ["string", "null"]},
                "source_url": {
                    "bsonType": ["string", "null"]},
                "status": {
                    "bsonType": "object",
                    # "required": ["download", "updated", "extracted", "transformed"],
                    "properties": {
                        "download" : {
                            "bsonType" : "bool"},
                        "uploaded": {
                            "bsonType": "bool"},
                        "extracted": {
                            "bsonType": "bool"},
                        "transformed": {
                            "bsonType": "bool"}
                    }
                },
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