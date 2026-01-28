import os
from pathlib import Path
from typing import Optional, Self

import pandas as pd
from dotenv import load_dotenv

from core import utils
from core.db import MongoDbHelper
from core.extract import TZ_NAME, ExtractorTemplate
from core.logger import getLogger

lg = getLogger("mctr")
load_dotenv()
MGDB_CONNECTION_STR = os.getenv(
    "MGDB_CONNECTION_STR", "mongodb://localhost:27017/default_db"
)
MGDB_COLL_INPUT_LEADINGORDERS = "input_raw_dw_leadingorders"


class LeadingOrderExtractor(ExtractorTemplate):
    dt_columns = [
        "engine_created_date",
        "engine_stage_date",
        "engine_output_date",
    ]
    str_columns = [
        "time_since_new",
        "time_since_overhaul",
        "cycles_since_new",
        "time_since_last_visit",
        "cycles_since_last_visit",
    ]

    def __init__(
        self,
        conn_str: str,
        input_fpath: Path,
        collection_name: str = MGDB_COLL_INPUT_LEADINGORDERS,
    ):
        self.db = MongoDbHelper(
            connection_str=conn_str,
            collection_name=collection_name,
            batch_size=1000,
        )
        self.input_fpath = input_fpath

    def connect_db(self) -> Self:
        self.db.connect()
        self.db.init_collection(index_names=["data_hash"])
        return self

    def load_input_file(self, input_fpath: Optional[Path] = None) -> Self:
        path_to_load = input_fpath or self.input_fpath
        match True:
            case _ if path_to_load.name.endswith(".json.gz"):
                lg.info(f"Extracting gzipped JSON file: {path_to_load}")
                self.load_data_from_json_gz(path_to_load)
            case _ if path_to_load.name.endswith(".json"):
                lg.info(f"Extracting JSON file: {path_to_load}")
                self.load_json(path_to_load)
            case _ if path_to_load.name.endswith(".csv.gz"):
                lg.info(f"Extracting gzipped CSV file: {path_to_load}")
                self.load_data_from_csv_gz(path_to_load)
            case _ if path_to_load.name.endswith(".csv"):
                lg.info(f"Extracting CSV file: {path_to_load}")
                self.load_csv(path_to_load)
            case _:
                raise ValueError(f"Unsupported file type: {path_to_load}")
        return self

    def clean_column_names(self, dfin: pd.DataFrame):
        return super().clean_column_names(dfin)

    def clean_dates(self, dfin: pd.DataFrame) -> pd.DataFrame:
        return super().clean_dates(dfin, TZ_NAME)

    def clean_data(self, dfin: pd.DataFrame) -> pd.DataFrame:
        df = dfin.copy()
        df = self.clean_dates(df)

        return df

    def run(self):
        self.connect_db()
        self.load_input_file()
        self.df = self.clean_data(self.df)
        data = self.convert_df_to_dict_list(self.df, delete_empty=True)
        inserted = self.db.insert_data_chunked(data)
        lg.info(
            f"Data seeding completed. {inserted} documents inserted into '{self.db.collection.name}'."
        )


def main():
    lg.info("etl entrypoint.py is running...")
    fpath = utils.get_resource_file("mctr.lo.extractor.*.json.gz")
    loe = LeadingOrderExtractor(conn_str=MGDB_CONNECTION_STR, input_fpath=fpath)
    loe.run()


if __name__ == "__main__":
    main()
