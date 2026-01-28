import datetime
import logging
import re
import time
from pathlib import Path
from typing import Sequence

import pandas as pd
import pymongo as pymg
from django.conf import settings
from django.core.files import File
from django.db.models import Model as DjangoModel
from main.utils import (
    get_datetime_str,
    get_utc_timestamp_now,
    parse_mongo_uri,
    sanitize_filename,
)
from recon.enums import ChoicesReportStatus as CRS
from recon.etl.core.utils import date_extractor, timing_decorator
from pymongo import MongoClient

MATR_CONF = settings.MATR_CONF
OUTPUT_COLUMNS_MAPPING = MATR_CONF.MATR_OUTPUT_COLUMNS_MAPPING
KW_PJ = MATR_CONF.MATR_OUTPUT_KW_PIECEJOB

MGDB_CONNX = settings.MGDB_CONNECTION_STR
MGDB = parse_mongo_uri(MGDB_CONNX)
MGDB_COLLECTION = MATR_CONF.MGDB_COLLECTION
MGDB_COLLECTION_ESN_LIST = MATR_CONF.MGDB_COLLECTION_ESN_LIST

lg = logging.getLogger("django")


def get_or_create_collection(
    client: MongoClient,
    database_name: str,
    collection_name: str,
    timeseries: dict = {
        "timeField": "timestamp",
        "metaField": "metadata",
        "granularity": "seconds",
    },
) -> None:
    db = client[database_name]
    if collection_name not in db.list_collection_names():
        lg.warning(f"creating {collection_name=}")
        db.create_collection(
            collection_name,
            timeseries=timeseries,
        )
    return db.get_collection(collection_name)


class MaterialsProcessor:
    def __init__(self) -> None:
        self.fpath = None
        self.i_po_start, self.i_po_end = None, None
        self.ind_start, self.ind_end = None, None
        self.i_qty_start, self.i_qty_end = None, None
        self.engines_indices = []

    @staticmethod
    def find_indices_po_edd(df: pd.DataFrame) -> tuple[int, int]:
        n = len(df.columns)
        i_start = 0
        i_end = 0
        for i, col in enumerate(df.columns):
            if "po no" in col.casefold():
                i_start = i
                break
        for i, col in enumerate(reversed(df.columns)):
            if "edd" in col.casefold():
                i_end = i
                break
        return (i_start, n - i_end)

    @staticmethod
    def find_indices_index(df: pd.DataFrame) -> tuple[int, int]:
        i_start = None
        i_end = None
        for i in range(len(df.columns)):
            col = df.columns[i]
            if i_start is None:
                if "part number" not in col.casefold():
                    continue
                else:
                    i_start = i
                    # print(f"left pointer found! {i_start=}")

            elif i_end is None:
                if "sort strin" in col.casefold():
                    i_end = i + 1
                    # print(f"right pointer found! {i_end=}")
                    break

        return (i_start, i_end)

    @staticmethod
    def find_indices_quantities(df: pd.DataFrame) -> tuple[int, int]:
        i_start = None
        i_end = None
        for i in range(len(df.columns)):
            col = df.columns[i]
            if i_start is None:
                if "max" not in col.casefold():
                    continue
                else:
                    i_start = i
                    # print(f"left pointer found! {i_start=}")

            elif i_end is None:
                if "tqs" in col.casefold():
                    i_end = i + 1
                    # print(f"right pointer found! {i_end=}")
                    break

        return (i_start, i_end)

    @staticmethod
    def find_indices_engines(
        df: pd.DataFrame, starter_index: int, end_index: int
    ) -> tuple[int]:
        first_engine_index = starter_index
        if df.columns[first_engine_index].casefold() == list(KW_PJ.keys())[0]:
            first_engine_index += 1
        engines_indices = []
        for i in range(first_engine_index, end_index):
            if "po no" in df.columns[i].casefold():
                break
            engines_indices.append(i)
        return engines_indices

    @staticmethod
    def find_indices_piece_job(df: pd.DataFrame) -> int | None:
        original_colname = list(KW_PJ.keys())[0]
        subs_colname = KW_PJ[original_colname]
        for i, col in enumerate(df.columns):
            if len(col) == 3 and "tqs" == col.casefold():
                piece_job_index = i + 1
        if original_colname.casefold() in df.columns[piece_job_index].casefold():
            lg.debug(f"{subs_colname} found")
            return piece_job_index
        return None

    @staticmethod
    def get_engines(indices: list[int], df: pd.DataFrame) -> list[str]:
        return df.columns[indices].tolist()

    def get_engine_shortagelist(
        self, dfin: pd.DataFrame, engine_index: int
    ) -> pd.DataFrame:
        i_po_start, i_po_end = self.i_po_start, self.i_po_end
        ind_start, ind_end = self.ind_start, self.ind_end
        i_qty_start, i_qty_end = self.i_qty_start, self.i_qty_end

        esn = dfin.columns[engine_index]
        df_l1 = dfin.iloc[:, ind_start:ind_end]
        df_l2 = dfin.iloc[:, i_qty_start:i_qty_end].copy()
        for c in df_l2.columns:
            df_l2[c] = pd.to_numeric(df_l2[c], downcast="integer", errors="coerce")
        df_l3 = dfin.iloc[:, i_po_start:i_po_end]
        df_engine = dfin.iloc[:, [engine_index]]
        df_engine.columns = ["engine_qty_shortage"]
        df = pd.concat([df_l1, df_l2, df_l3, df_engine], axis=1)
        df = df[df["engine_qty_shortage"] != 0.0]
        df["esn"] = esn

        df = df[OUTPUT_COLUMNS_MAPPING.keys()]
        df.rename(columns=OUTPUT_COLUMNS_MAPPING, inplace=True)
        return df

    @timing_decorator
    def parse_sap_input(self, fpath: Path | None = None) -> pd.DataFrame:
        if fpath is None:
            fpath = self.fpath

        df = pd.read_csv(fpath, sep="|")
        df.columns = df.columns.astype(str)
        cols_selected = {}
        i = 0
        for col in df.columns:
            col_ = col.strip()
            if not col_ or ("Unnamed: " in col_):
                col_ = f"unnamed_col{i:04d}"
                i += 1
                while col_ in cols_selected.values():
                    i += 1
                    col_ = f"unnamed_col{i:04d}"
            cols_selected[col] = col_

        df.rename(columns=cols_selected, inplace=True)

        return df

    @timing_decorator
    def export_to_excel(
        self,
        df,
        engine_column_indices: Sequence[int],
        out_fpath: Path,
        piece_job_index: int | None = None,
    ) -> None:
        with pd.ExcelWriter(out_fpath) as writer:
            df.to_excel(writer, sheet_name="raw")
            empty_engines = []
            for i, eng in enumerate(engine_column_indices):
                dfshort = self.get_engine_shortagelist(df, eng)
                if dfshort.empty:
                    esn = df.columns[eng]
                    empty_engines.append({"empty_dataframe": esn})
                else:
                    esn = "".join(dfshort["esn"].unique())
                    dfshort.to_excel(writer, sheet_name=esn, index=False)
            if piece_job_index is not None:
                original_colname = list(KW_PJ.keys())[0]
                subs_colname = KW_PJ[original_colname]
                dfshort = self.get_engine_shortagelist(df, piece_job_index)
                dfshort["esn"] = subs_colname
                dfshort.to_excel(writer, sheet_name=subs_colname, index=False)
            dfempty = pd.DataFrame(empty_engines)
            dfempty.to_excel(writer, sheet_name="no_data", index=True)
        lg.info(f"export to excel file done: {out_fpath}")

    def run(self, input_fpath: Path, outname: str = "output-excelwriter") -> Path:
        if not input_fpath.is_file():
            raise FileNotFoundError(f"{input_fpath=}")
        self.fpath = input_fpath
        self.df = self.parse_sap_input(self.fpath)
        df = self.df.copy()
        self.i_po_start, self.i_po_end = self.find_indices_po_edd(df)
        self.ind_start, self.ind_end = self.find_indices_index(df)
        self.i_qty_start, self.i_qty_end = self.find_indices_quantities(df)
        self.engines_indices = self.find_indices_engines(
            df, self.i_qty_end, len(df.columns) + 1
        )
        self.i_piece_job = self.find_indices_piece_job(df)

        outname = sanitize_filename(outname)
        if not outname:
            outname = "output-excelwriter"
        output_fpath = (
            MATR_CONF.OUTPUT_DIRPATH_ZMMR3010 / f"{outname}-{get_datetime_str()}.xlsx"
        )

        self.write_to_mgdb(
            self.df,
            engine_column_indices=self.engines_indices,
            piece_job_index=self.i_piece_job,
        )

        self.export_to_excel(
            self.df,
            engine_column_indices=self.engines_indices,
            out_fpath=output_fpath,
            piece_job_index=self.i_piece_job,
        )

        return output_fpath

    def readback_mgdb(self):
        with MongoClient(MGDB_CONNX) as client:
            db = client[MGDB.db]
            collection = db[MGDB_COLLECTION]
            # optimize query by selecting only a window of n years
            start_time = datetime.datetime(
                get_utc_timestamp_now().year - MATR_CONF.MGDB_WINDOW_YEARS,
                1,
                1,
                0,
                0,
                0,
            )
            query = {"timestamp": {"$gte": start_time}}
            results = collection.find(query).sort("timestamp", pymg.DESCENDING).limit(1)
            try:
                doc = results.next()
                df = pd.DataFrame(doc["items"])
                return df
            except StopIteration:
                return pd.DataFrame()

    def insert_to_mgdb_collection(
        self,
        collection,
        df: pd.DataFrame,
        reportname: str = "zmmr3010",
        df_type: str = "raw",
        esn: str = "_all",
        timestamp: datetime.datetime = get_utc_timestamp_now(),
    ):
        input_filename = "null"
        input_file_date = datetime.datetime.now(datetime.timezone.utc)
        if self.fpath is not None and isinstance(self.fpath, Path):
            input_filename = self.fpath.name
            try:
                input_file_date = date_extractor(self.fpath.name)
            except Exception as e:
                lg.debug(f"date_extractor failed for {self.fpath.name=}: {e}")
                pass

        data_dict = df.to_dict(orient="records")
        insert_result = collection.insert_one(
            {
                "timestamp": timestamp,
                "metadata": {
                    "reportname": reportname,
                    "df_type": df_type,
                    "esn": esn,
                    "input_filename": input_filename,
                    "input_file_date": input_file_date,
                },
                "df": data_dict,
            }
        )

        return insert_result

    def insert_to_mgdb_esn_list(
        self,
        esn_list: list,
        collection,
        timestamp: datetime.datetime = get_utc_timestamp_now(),
        reportname: str = "zmmr3010",
    ) -> None:
        input_filename = "null"
        input_file_date = datetime.datetime.now(datetime.timezone.utc)
        if self.fpath is not None and isinstance(self.fpath, Path):
            input_filename = self.fpath.name
            try:
                input_file_date = date_extractor(self.fpath.name)
            except Exception as e:
                lg.debug(f"date_extractor failed for {self.fpath.name=}: {e}")
                pass

        collection.insert_one(
            {
                "timestamp": timestamp,
                "metadata": {
                    "reportname": reportname,
                    "input_filename": input_filename,
                    "input_file_date": input_file_date,
                },
                "esn_list": esn_list,
            }
        )

    @timing_decorator
    def write_to_mgdb(
        self,
        df,
        engine_column_indices: Sequence[int],
        piece_job_index: int | None = None,
    ):
        with MongoClient(MGDB_CONNX) as client:
            collection = get_or_create_collection(
                client=client,
                database_name=MGDB.db,
                collection_name=MGDB_COLLECTION,
            )
            mgdb_results = []
            ## Raw df with everything is > 16MB, too big for a
            ## single document in MongoDB, so we skip this part
            # mgdb_results = self.insert_to_mgdb_collection(
            #     results=mgdb_results,
            #     collection=collection,
            #     df=df,
            #     df_type="raw",
            #     esn="_all",
            # )

            timestamp = get_utc_timestamp_now()

            empty_engines = []
            esn_list = []
            for i, eng in enumerate(engine_column_indices):
                dfshort = self.get_engine_shortagelist(df, eng)
                if dfshort.empty:
                    esn = df.columns[eng]
                    empty_engines.append({"empty_dataframe": esn})
                else:
                    esn = "".join(dfshort["esn"].unique())
                    insert_result = self.insert_to_mgdb_collection(
                        collection=collection,
                        df=dfshort,
                        df_type="esn",
                        esn=esn,
                        timestamp=timestamp,
                    )
                    mgdb_results.append(insert_result)
                    esn_list.append(esn)

            if piece_job_index is not None:
                original_colname = list(KW_PJ.keys())[0]
                subs_colname = KW_PJ[original_colname]
                dfshort = self.get_engine_shortagelist(df, piece_job_index)
                dfshort["esn"] = subs_colname
                insert_result = self.insert_to_mgdb_collection(
                    collection=collection,
                    df=dfshort,
                    df_type=subs_colname,
                    esn=subs_colname,
                    timestamp=timestamp,
                )
                mgdb_results.append(insert_result)
                esn_list.append(subs_colname)

            dfempty = pd.DataFrame(empty_engines)
            insert_result = self.insert_to_mgdb_collection(
                collection=collection,
                df=dfempty,
                df_type="no_data",
                esn="no_data",
                timestamp=timestamp,
            )
            mgdb_results.append(insert_result)

            collection_esn_list = get_or_create_collection(
                client=client,
                database_name=MGDB.db,
                collection_name=MGDB_COLLECTION_ESN_LIST,
            )
            self.insert_to_mgdb_esn_list(
                esn_list=esn_list, collection=collection_esn_list, timestamp=timestamp
            )
