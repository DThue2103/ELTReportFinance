import os

from dotenv import load_dotenv
from dataclasses import dataclass

@dataclass
class MongoDBConfig():
    uri : str
    db_name : str
    collection : str = "report_finance"

def get_database_config():
    load_dotenv()
    config = {
        "mongodb": MongoDBConfig(
            uri = os.getenv("MONGO_URI"),
            db_name = os.getenv("MONGO_DB_NAME")
        )
    }
    return config

if __name__ == '__main__':
    config = get_database_config()
    # config = get_spark_config()
    print(config)