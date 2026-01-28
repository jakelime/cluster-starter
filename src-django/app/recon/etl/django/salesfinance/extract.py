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
MGDB_COLL_INPUT_SALES = "input_raw_dw_sales"
SALES_FIELD_PARSERS = settings.SALES_CONF.SALES_FIELD_PARSERS
SALES_COLUMN_TO_ENGINE_DB_MAP = settings.SALES_CONF.SALES_COLUMN_TO_ENGINE_DB_MAP

EXCEL_EXTENSIONS = {".xlsx", ".xlsm", ".xlsb", ".xls"}

CONFIG = {
    "cfm56-excel-parser": {
        "pandas": {
            "sheet_name": "CFM56 Engine details",
            "header": 4,
        },
        "drop_na_count": 50,  # Drop rows with more than n NaN values, 0 to disable
        "drop_na_columns": ["uuid"],  # Drop rows with NaN values in these columns
        "dt_columns": [
            "fct_input_month",
            "engine_output_forecast_month_see_note_for_lion_air",
            "induction_month_stea_engines",
            "actual_input_received_date",
            "actual_induction_date",
        ],
        "str_columns": [
            "uuid",
            "esn",
            "customer",
            "engine_type",
            "program_type",
            "facility",
            "certainty_of_engine_input",
            "engine_status",
        ],
    },
    "leap-excel-parser": {
        "pandas": {
            "sheet_name": "LEAP Engine details",
            "header": 4,
        },
        "drop_na_count": 50,  # Drop rows with more than n NaN values, 0 to disable
        "drop_na_columns": ["uuid"],  # Drop rows with NaN values in these columns
        "dt_columns": [
            "fct_input_month",
            "engine_output_forecast_month_see_note_for_lion_air",
            "induction_month_stea_engines",
            "actual_input_received_date",
            "actual_induction_date",
        ],
        "str_columns": [
            "uuid",
            "esn",
            "customer",
            "engine_type",
            "program_type",
            "facility",
            "certainty_of_engine_input",
            "engine_status",
        ],
    },
}


class SalesExtractor(ExtractorTemplate):
    dt_columns: Optional[list] = None
    str_columns: Optional[list] = None

    def __init__(
        self,
        conn_str: str,
        input_fpath: Path,
        collection_name: str = MGDB_COLL_INPUT_SALES,
        column_to_engine_db_map: dict[str, str] = SALES_COLUMN_TO_ENGINE_DB_MAP,
        config: Optional[dict] = None,
    ):
        self.db = MongoDbHelper(
            connection_str=conn_str,
            collection_name=collection_name,
            batch_size=1000,
        )
        self.load_config(config)
        self.input_fpath = input_fpath
        self.column_to_engine_db_map = column_to_engine_db_map
        self.column_mapper = column_to_engine_db_map

    def connect_db(self) -> Self:
        self.db.connect()
        self.db.init_collection(index_names=["data_hash"])
        return self

    def load_input_file(
        self,
        input_fpath: Optional[Path] = None,
        pandas_kwargs: Optional[dict] = None,
    ) -> Self:
        path_to_load = input_fpath or self.input_fpath
        file_suffix = path_to_load.suffix.casefold()

        match file_suffix:
            # Case 1: Handle all Excel extensions
            case suffix if suffix in EXCEL_EXTENSIONS:
                lg.info(f"Preparing to parse Excel file: {path_to_load}")
                self.load_excel(input_fpath=path_to_load, pandas_kwargs=pandas_kwargs)
            # Case N (Wildcard): Handle all unsupported file types
            case _:
                raise ValueError(f"Unsupported file type: {path_to_load}")

        return self

    def clean_column_names(self, dfin: pd.DataFrame):
        return super().clean_column_names(dfin)

    def clean_dates(self, dfin: pd.DataFrame, dt_columns: list = []) -> pd.DataFrame:
        df = dfin.copy()
        if dt_columns:
            for dt_col in dt_columns:
                MONTH_ONLY = (
                    "fct_input_month",
                    "induction_month",
                    "engine_output_forecast_month",
                    "revenue_forecast_by_month",
                )
                FULL_DATE = (
                    "actual_input_received_date",
                    "actual_induction_date",
                    "actual_output_date_shipment",
                    "plan_test_date",
                )
                col_lower = dt_col.casefold()
                if any(substring in col_lower for substring in MONTH_ONLY):
                    format = "%b-%y"
                    lg.info(
                        f"[FORMAT:{format}] Converting column '{dt_col}' to datetime with timezone {TZ_NAME}."
                    )
                    try:
                        df[dt_col] = pd.to_datetime(
                            df[dt_col],
                            format=format,
                            errors="coerce",
                        ).dt.tz_localize(TZ_NAME)
                    except Exception as e:
                        lg.error(
                            f"Error converting column '{dt_col}' to datetime; {e=}",
                        )
                        df[dt_col] = pd.NaT  # Set to NaT if conversion fails

                    continue
                elif any(substring in col_lower for substring in FULL_DATE):
                    format = "%d-%b-%y"
                    lg.info(
                        f"[FORMAT:{format}] Converting column '{dt_col}' to datetime with timezone {TZ_NAME}."
                    )
                    try:
                        df[dt_col] = pd.to_datetime(
                            df[dt_col],
                            format=format,
                            errors="coerce",
                        ).dt.tz_localize(TZ_NAME)
                    except Exception as e:
                        lg.error(
                            f"Error converting column '{dt_col}' to datetime; {e=}",
                        )
                        df[dt_col] = pd.NaT  # Set to NaT if conversion fails
                    continue
                else:
                    lg.info(
                        f"[AUTO] Converting column '{dt_col}' to datetime with timezone {TZ_NAME}."
                    )
                    try:
                        df[dt_col] = pd.to_datetime(
                            df[dt_col], errors="coerce"
                        ).dt.tz_localize(TZ_NAME)
                    except Exception as e:
                        lg.error(
                            f"Error converting column '{dt_col}' to datetime; {e=}",
                        )
                        df[dt_col] = pd.NaT  # Set to NaT if conversion fails
        return df

    def clean_str(self, dfin: pd.DataFrame, str_columns: list = []) -> pd.DataFrame:
        """
        Convert specified columns to string, stripping whitespace.
        """
        df = dfin.copy()
        if str_columns:
            for str_col in str_columns:
                try:
                    df[str_col] = df[str_col].astype(str).str.strip()
                    df[str_col] = df[str_col].replace("nan", "")
                except Exception as e:
                    lg.error(f"Error converting column '{str_col}' to string; {e=}")
                    df[str_col] = ""  # Set to empty string if conversion fails
        return df

    def clean_data(self, dfin: pd.DataFrame) -> pd.DataFrame:
        df = dfin.copy()
        drop_na_count = self.config.get("drop_na_count", 50)
        drop_na_columns = self.config.get("drop_na_columns", ["uuid"])
        dt_columns = self.config.get("dt_columns", [])
        str_columns = self.config.get("str_columns", [])
        df = self.clean_drop_na(
            df,
            drop_na_count=drop_na_count,
            drop_na_columns=drop_na_columns,
        )
        df = self.clean_dates(df, dt_columns=dt_columns)
        df = self.clean_str(df, str_columns=str_columns)

        return df

    def clean_drop_na(
        self,
        dfin: pd.DataFrame,
        drop_na_count: int = 50,
        drop_na_columns: list[str] = [],
    ) -> pd.DataFrame:
        """
        Drop rows with more than `drop_na_count` NaN values.
        """
        df = dfin.copy()
        if drop_na_count > 0:
            df = df.dropna(thresh=drop_na_count)
        if drop_na_columns:
            df = df.dropna(subset=drop_na_columns)

        lg.info(f"{df.shape=} after dropping {drop_na_count=}, {drop_na_columns=}")
        return df

    def run(self) -> int:
        self.connect_db()
        pandas_kwargs = self.config.get("pandas", {})

        self.load_input_file(pandas_kwargs=pandas_kwargs)
        inserted = 0
        df = self.df.copy()
        df = self.clean_column_names(df)
        df = self.clean_data(df)
        data = self.convert_df_to_dict_list(df, delete_empty=True)
        inserted += self.db.insert_data_chunked(data)
        lg.info(
            f"Data seeding completed. {inserted} documents inserted into '{self.db.collection.name}'."
        )
        return inserted


def main_example(
    conn_str: Optional[str] = None, input_fpath: Optional[Path] = None
) -> None:
    """Main entry point for running the SalesExtractor."""
    conn_str = conn_str or MGDB_CONNECTION_STR
    fpath = input_fpath or utils.get_resource_file("mctr.lo.extractor.*.json.gz")
    # This is an example entry point for running the extractor.
    # It can be used in a Django management command or as a standalone script.
    lg.info("etl entrypoint.py is running...")
    cfm_sales = SalesExtractor(
        conn_str=conn_str,
        input_fpath=fpath,
        config=CONFIG.get("cfm56-excel-parser"),
    )
    cfm_sales.run()

    leap_sales = SalesExtractor(
        conn_str=conn_str,
        input_fpath=fpath,
        config=CONFIG.get("leap-excel-parser"),
    )
    leap_sales.run()


if __name__ == "__main__":
    main_example()
