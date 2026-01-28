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
MGDB_COLL_INPUT_OPS = "input_raw_dw_ops"
OPS_FIELD_PARSERS = settings.OPS_CONF.OPS_FIELD_PARSERS
OPS_COLUMN_TO_ENGINE_DB_MAP = settings.OPS_CONF.OPS_COLUMN_TO_ENGINE_DB_MAP

EXCEL_EXTENSIONS = {".xlsx", ".xlsm", ".xlsb", ".xls"}

CONFIG = {
    "cfm56-excel-parser": {
        "pandas": {
            "sheet_name": "Engine Production Master File",
            "header": 3,
        },
        "drop_na_count": 0,  # Drop rows with more than n NaN values, 0 to disable
        "drop_na_columns": ["uuid"],  # Drop rows with NaN values in these columns
        "dt_columns": [
            "engine_input_date",
            "induction",
            "gate_1_completed",
            "gate_2_kit_date",
            "test_date_rigging",
            "pass_test_date",
            "pack_ready_date",
            "shipment_date",
            "delivered_date_customer",
        ],
        "str_columns": [
            "uuid",
            "esn",
            "customer",
            "engine_model",
            "shop_visit_scope",
            "status",
            "key_issues_impacting_tat",
            "remarks",
        ],
        "int_columns": [
            "gate_1_tat",
            "gross_tat",
            "net_tat",
        ],
    },
    "leap-engine-excel-parser": {
        "pandas": {
            "sheet_name": "LEAP Engine Master",
            "header": 3,
        },
        "drop_na_count": 0,  # Drop rows with more than n NaN values, 0 to disable
        "drop_na_columns": ["uuid"],  # Drop rows with NaN values in these columns
        "dt_columns": [
            "engine_input_date",
            "induction",
            "gate_1a_completed",
            "gate_1b_completed",
            "gate_2_kit_date",
            "gate_3a_start",
            "gate_3b_start_test_date_rigging",
            "pass_test_date",
            "pack_ready_date",
            "shipment_date",
        ],
        "str_columns": [
            "uuid",
            "esn",
            "customer",
            "engine_model",
            "job_number",
            "operator",
            "shop_visit_scope",
            "status",
            "key_issues_impacting_tat",
            "remarks",
        ],
        "num_columns": [
            "gross_tat",
            "net_tat",
            "tat_from_induction_to_pass_test",
            "g1a_gross_tat",
            "g1b_gross_tat",
            "g3a_gross_tat",
            "g3b_gross_tat",
            "engine_build_to_pack_and_ready",
            "engine_pass_test_to_pack_and_ready",
            "engine_testing_tat",
            "total_engine_manhours",
            "engine_rig_de_rig_hours",
            "engine_testing_hours",
            "engine_troubleshooting_hours",
            "total_testing",
        ],
    },
    "leap-module-excel-parser": {
        "pandas": {
            "sheet_name": "LEAP Module Master",
            "header": 3,
        },
        "drop_na_count": 0,  # Drop rows with more than n NaN values, 0 to disable
        "drop_na_columns": ["uuid"],  # Drop rows with NaN values in these columns
        "dt_columns": [
            "engine_input_date",
            "induction",
            "gate_1a_completed",
            "gate_1b_completed",
            "gate_2_kit_date",
            "g3_start",
            "pass_test_date",
            "pack_ready_date",
            "shipment_date",
        ],
        "str_columns": [
            "uuid",
            "esn",
            "module_sn",
            "customer",
            "engine_model",
            "job_number",
            "operator",
            "shop_visit_scope",
            "status",
            "key_issues_impacting_tat",
            "remarks",
        ],
        "num_columns": [
            "gross_tat",
            "net_tat",
            "g1a_gross_tat",
            "g1b_gross_tat",
            "g3_gross_tat",
        ],
    },
}


class OpsExtractor(ExtractorTemplate):
    dt_columns: Optional[list] = None
    str_columns: Optional[list] = None

    def __init__(
        self,
        conn_str: str,
        input_fpath: Path,
        collection_name: str = MGDB_COLL_INPUT_OPS,
        column_to_engine_db_map: dict[str, str] = OPS_COLUMN_TO_ENGINE_DB_MAP,
        config: Optional[dict] = None,
    ):
        self.db = MongoDbHelper(
            connection_str=conn_str,
            collection_name=collection_name,
            batch_size=1000,
        )
        self.config = config or CONFIG
        self.input_fpath = input_fpath
        self.column_to_engine_db_map = column_to_engine_db_map
        self.column_mapper = column_to_engine_db_map
        self.load_config()

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
                lg.info(
                    f"[FORMAT:%d-%b-%y] Converting column '{dt_col}' to datetime with timezone {TZ_NAME}."
                )
                try:
                    df[dt_col] = pd.to_datetime(
                        df[dt_col],
                        format="%d-%b-%y",
                        errors="coerce",
                    ).dt.tz_localize(TZ_NAME)
                except Exception as e:
                    lg.error(
                        f"Error converting column '{dt_col}' to datetime; {e=}",
                    )
                    df[dt_col] = pd.NaT  # Set to NaT if conversion fails
        return df

    def clean_nums(self, dfin: pd.DataFrame, num_columns: list = []) -> pd.DataFrame:
        """
        Convert specified columns to numeric, coercing errors to NaN.
        """
        df = dfin.copy()
        if num_columns:
            for num_col in num_columns:
                try:
                    df[num_col] = pd.to_numeric(df[num_col], errors="coerce")
                except Exception as e:
                    lg.error(f"Error converting column '{num_col}' to numeric; {e=}")
                    df[num_col] = pd.NA  # Set to NA if conversion fails
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
        num_columns = self.config.get("num_columns", [])
        str_columns = self.config.get("str_columns", [])
        df = self.clean_drop_na(
            df,
            drop_na_count=drop_na_count,
            drop_na_columns=drop_na_columns,
        )
        df = self.clean_dates(df, dt_columns=dt_columns)
        df = self.clean_nums(df, num_columns=num_columns)
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
    """Main entry point for running the OpsExtractor."""
    conn_str = conn_str or MGDB_CONNECTION_STR
    fpath = input_fpath or utils.get_resource_file("mctr.lo.extractor.*.json.gz")
    # This is an example entry point for running the extractor.
    # It can be used in a Django management command or as a standalone script.
    lg.info("etl entrypoint.py is running...")
    cfm_ops = OpsExtractor(
        conn_str=conn_str,
        input_fpath=fpath,
        config=CONFIG.get("cfm56-excel-parser"),
    )
    cfm_ops.run()

    leap_engine_ops = OpsExtractor(
        conn_str=conn_str,
        input_fpath=fpath,
        config=CONFIG.get("leap-engine-excel-parser"),
    )
    leap_engine_ops.run()

    leap_module_ops = OpsExtractor(
        conn_str=conn_str,
        input_fpath=fpath,
        config=CONFIG.get("leap-module-excel-parser"),
    )
    leap_module_ops.run()


if __name__ == "__main__":
    main_example()
