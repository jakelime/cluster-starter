import os

from core.db import MongoDbHelper
from core.logger import getLogger

from dotenv import load_dotenv

lg = getLogger("mctr")
load_dotenv()
MGDB_CONNECTION_STR = os.getenv(
    "MGDB_CONNECTION_STR", "mongodb://localhost:27017/default_db"
)
MGDB_COLL_INPUT_LEADINGORDERS = "input_raw_dw_leadingorders"


def main():
    lg.info("simulating etl entrypoint...")
    db = MongoDbHelper(
        connection_str=MGDB_CONNECTION_STR,
        collection_name=MGDB_COLL_INPUT_LEADINGORDERS,
        batch_size=1000,
    )
    db.connect()
    db.connect_to_collection()
    db.insert_one(
        {
            "name": "test",
            "description": "This is a test document",
            "created_at": "2023-10-01T12:00:00Z",
        }
    )


if __name__ == "__main__":
    main()
