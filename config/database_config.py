import os

from dotenv import load_dotenv
from dataclasses import dataclass


@dataclass
class MongoDBConfig():
    uri : str
    database : str
    collection : str = "report_finance"

def get_database_config():
    load_dotenv()
    config = {
        "mongodb": MongoDBConfig(
            uri = os.getenv("MONGO_URI"),
            database = os.getenv("MONGO_DB_NAME")
        )
    }
    return config

def get_spark_config():
    db_configs = get_database_config()
    return{
        "mongodb": {
            "uri": db_configs["mongodb"].uri,
            "database": db_configs["mongodb"].database,
            "collection": db_configs["mongodb"].collection
        }
    }

if __name__ == '__main__':
    config = get_database_config()
    # config = get_spark_config()
    print(config)