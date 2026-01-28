# This code is meant to be run from Django management command.
# Amend the import statements accordingly if you are running it in a different context.
import logging
import os
from pathlib import Path
from typing import Optional, Self

import pandas as pd
from django.conf import settings
from dotenv import load_dotenv
from main.utils import parse_mongo_uri
from recon.etl.core import utils
from recon.etl.core.db import MongoDbHelper
from recon.etl.core.extract import TZ_NAME, ExtractorTemplate

lg = logging.getLogger("django")
load_dotenv()
MGDB_CONNECTION_STR = os.getenv(
    "MGDB_CONNECTION_STR", "mongodb://localhost:27017/default_db"
)
MGDB_CONNX = settings.MGDB_CONNECTION_STR
MGDB = parse_mongo_uri(MGDB_CONNX)
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
        df = dfin.copy()
        for dt_col in self.dt_columns:
            df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce").dt.tz_convert(
                TZ_NAME
            )
        return df

    def clean_data(self, dfin: pd.DataFrame) -> pd.DataFrame:
        df = dfin.copy()
        df = self.clean_dates(df)
        return df

    def run(self) -> int:
        self.connect_db()
        self.load_input_file()
        self.df = self.clean_data(self.df)
        data = self.convert_df_to_dict_list(self.df, delete_empty=True)
        inserted = self.db.insert_data_chunked(data)
        lg.info(
            f"Data seeding completed. {inserted} documents inserted into '{self.db.collection.name}'."
        )
        return inserted


def main_example():
    # This is an example entry point for running the extractor.
    # It can be used in a Django management command or as a standalone script.
    lg.info("etl entrypoint.py is running...")
    fpath = utils.get_resource_file("mctr.lo.extractor.*.json.gz")
    loe = LeadingOrderExtractor(conn_str=MGDB_CONNECTION_STR, input_fpath=fpath)
    loe.run()


if __name__ == "__main__":
    main_example()
