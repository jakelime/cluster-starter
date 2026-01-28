# Extract
# etl - extract, transform, load
# extract will take in input file perform first level raw cleaning,
# and load it into "e" collection of the database, i.e. raw_input_collection

import datetime
import gzip
import hashlib
import json
import logging
import os
import re
import shutil
import warnings
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Self

import pandas as pd
from dotenv import load_dotenv

load_dotenv()
lg = logging.getLogger("django")

TZ_NAME = os.getenv("DJANGO_TIMEZONE", "Asia/Singapore")


def get_time_now() -> pd.Timestamp:
    """returns the current time in the configured timezone (default UTC)"""
    return pd.Timestamp(datetime.datetime.now(), tz=TZ_NAME)


def compute_row_hash(data_dict: dict) -> str:
    """
    Computes a unique SHA-256 hash for a dictionary by first converting
    it to a canonical JSON string.

    Args:
        data_dict: The dictionary representing a row of data.

    Returns:
        A SHA-256 hash string.
    """

    # 1. Handle non-serializable types (like Pandas Timestamps)
    # Convert Timestamp objects to ISO 8601 strings
    # This custom serialization is necessary because the default json.dumps
    # can't handle pandas.Timestamp objects directly.
    def custom_json_serializer(obj):
        if isinstance(obj, pd.Timestamp):
            # Convert to string for stable hashing, e.g., '2023-12-04T00:00:00+08:00'
            return obj.isoformat()
        elif isinstance(obj, datetime.datetime):
            # Also handle standard datetime objects if they were somehow introduced
            return obj.isoformat()
        # Fallback for other non-serializable types if needed
        raise TypeError(
            f"Object of type {obj.__class__.__name__} is not JSON serializable"
        )

    # 2. Convert dictionary to a canonical JSON string
    #   - sort_keys=True: Ensures the same dict content always produces the same string.
    #   - separators=(',', ':'): Removes unnecessary whitespace for conciseness.
    #   - default=custom_json_serializer: Uses the function above for Timestamps.
    json_string = json.dumps(
        data_dict, sort_keys=True, separators=(",", ":"), default=custom_json_serializer
    ).encode("utf-8")

    # 3. Compute the SHA-256 hash
    return hashlib.sha256(json_string).hexdigest()


def get_or_create_temp_dir() -> Path:
    """
    Create a temporary folder in the resources directory.
    The folder will be named 'temp' and will be created in the resources directory.
    If the folder already exists, it will be removed first.
    """
    base_dir = Path(__file__).resolve().parent
    temp_folder = base_dir.parent / "temp"
    if not temp_folder.exists():
        try:
            temp_folder.mkdir(parents=True, exist_ok=True)
            lg.info(f"Temporary folder created at: {temp_folder}")
        except OSError as e:
            lg.error(f"Error creating temporary folder: {e=}")
            raise
    return temp_folder


def extract_from_gzip(
    resource_path: Optional[Path] = None, resource_name: Optional[str] = None
) -> Path | None:
    """
    Get a resource from a gzip file.
    If `resource_path` is provided, it should be a Path object pointing to the gzip file, or the parent folder.
    If `resource_name` is provided, it should be the name of the resource to look in the resource_path folder.
    """
    if resource_path is None and resource_name is None:
        raise ValueError("Either resource_path or resource_name must be provided.")
    elif resource_path is not None and resource_name is not None:
        if resource_path.is_file():
            raise ValueError(
                "Illegal argument combination: provide either resource_path or resource_name, not both."
            )
        else:
            if not resource_path.is_dir():
                raise ValueError(
                    f"Provided resource_path {resource_path} is not a directory. (looking for {resource_name=})"
                )
            resource_path = resource_path / resource_name
    elif resource_path is None and resource_name is not None:
        raise ValueError(
            "resource_path must be provided if resource_name is specified."
        )

    input_gz_path = resource_path
    output_csv_path = get_or_create_temp_dir() / resource_path.stem
    try:
        with gzip.open(input_gz_path, "rb") as f_in:
            with open(output_csv_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        lg.info(f"File successfully unzipped to: {output_csv_path}")
        return output_csv_path
    except FileNotFoundError:
        lg.error(f"Error: File not found - {input_gz_path}")
    except Exception as e:
        lg.error(f"An error occurred: {e}")

    return None


def convert_to_snake_case(name: str) -> str:
    """
    Converts a column name into a PEP8-compliant snake_case variable name.

    This function performs the following steps for each name:
    1. Converts the name to lowercase.
    2. Replaces symbols, newlines, parentheses, quotes, and slashes with spaces.
    3. Replaces sequences of spaces with a single underscore.
    4. Strips any leading or trailing underscores.

    Args:
        name: A original column name string.

    Returns:
        A cleaned, snake_case string.
    """
    chars_to_replace = r"[^\w\s]"

    name = name.lower().strip()
    cleaned_name = re.sub(chars_to_replace, " ", name)
    snake_case_name = re.sub(r"\s+", "_", cleaned_name)
    snake_case_name = re.sub(r"_+", "_", snake_case_name)
    snake_case_name = snake_case_name.strip("_")

    return snake_case_name if snake_case_name else None


class ExtractorTemplate(ABC):
    config: Optional[dict] = None
    df: Optional[pd.DataFrame] = None
    collection_name: str = "input_raw_default"
    column_mapper: Optional[dict] = None
    dt_columns: Optional[list] = None
    str_columns: Optional[list] = None
    input_fpath: Optional[Path] = None
    df_sheets: Optional[dict[str, pd.DataFrame]] = None

    def unpack_gz(self, gz_filepath: Path) -> Path:
        path = extract_from_gzip(gz_filepath)
        if not path:
            raise RuntimeError(f"unpack_gz failed. {gz_filepath=}")
        return path

    def load_config(self, config: Optional[dict] = None) -> Self:
        """
        loads configuration from dict
        loads configuration from list of str for datetime columns
        loads configuration from list of str for str columns
        """
        if config is not None:
            self.config = config
        if self.config is not None:
            dt_columns = self.config.get("dt_columns", [])
            if dt_columns:
                self.dt_columns = dt_columns

            str_columns = self.config.get("str_columns", [])
            if str_columns:
                self.str_columns = str_columns

        return self

    def load_csv(self, input_fpath: Optional[Path] = None) -> Self:
        """
        Loads data from a CSV file.

        :param input_fpath: Optional path to a CSV file. If not provided, uses self.input_fpath.
        :return: A pandas DataFrame with the CSV data.
        """
        path_to_load = input_fpath or self.input_fpath
        if not path_to_load or not os.path.exists(path_to_load):
            lg.error(f"CSV file not found: {path_to_load=}")
            raise SystemExit(5)

        lg.info(f"Reading CSV: {path_to_load}")
        try:
            # Keep simple; let pandas infer dtypes. Convert NaN -> None later.
            df = pd.read_csv(path_to_load, low_memory=False)
            lg.info(f"CSV loaded: {len(df.index)} rows, {len(df.columns)} columns")
            self.df = df
            return self
        except Exception as e:
            raise RuntimeError("Failed to read CSV.") from e

    def load_excel(
        self,
        *,
        input_fpath: Optional[Path] = None,
        pandas_kwargs: Optional[dict] = None,
    ) -> Self:
        """
        Loads data from an excel file.

        :param input_fpath: Optional path to an excel file. If not provided, uses self.input_fpath.
        :return: A pandas DataFrame with the excel data.
        """
        path_to_load = input_fpath or self.input_fpath
        if not path_to_load or not os.path.exists(path_to_load):
            lg.error(f"Excel file not found: {path_to_load=}")
            raise SystemExit(5)

        lg.info(f"parsing path={path_to_load}")

        try:
            with warnings.catch_warnings():
                # Suppress openpyxl warning
                warnings.filterwarnings(
                    "ignore", category=UserWarning, module="openpyxl"
                )

                # KISS: let pandas infer dtypes
                # Convert NaN -> None later.
                df = pd.read_excel(path_to_load, **pandas_kwargs)
                # From pandas docs: sheet_name = str, int, list, or None, default 0
                loaded_sheet = pandas_kwargs.get("sheet_name", 0)
                lg.info(
                    f"sheet({loaded_sheet}) loaded using {pandas_kwargs}: {df.shape=}"
                )

                self.df = df
            return self
        except Exception as e:
            raise RuntimeError("Failed to read excel.") from e

    def load_json(self, input_fpath: Optional[Path] = None) -> Self:
        """
        Loads data from a JSON file.

        :param input_fpath: Optional path to a JSON file. If not provided, uses self.input_fpath.
        :return: A pandas DataFrame with the JSON data.
        """
        path_to_load = input_fpath or self.input_fpath
        if not path_to_load or not os.path.exists(path_to_load):
            lg.error(f"JSON file not found: {path_to_load=}")
            raise SystemExit(5)

        lg.info(f"Reading JSON: {path_to_load}")
        try:
            with open(path_to_load, "r") as f:
                data = json.load(f)
                first_key = next(iter(data))
                first_value = data[first_key]
                df = pd.DataFrame(first_value)
            lg.info(f"Data parsed from JSON. {df.shape=}")
            self.df = df
            return self
        except Exception as e:
            raise RuntimeError("Failed to read JSON.") from e

    def load_data_from_json_gz(self, gz_filepath: Path) -> Self:
        path = self.unpack_gz(gz_filepath)
        return self.load_json(path)

    def load_data_from_csv_gz(self, gz_filepath: Path) -> Self:
        path = self.unpack_gz(gz_filepath)
        return self.load_csv(path)

    def clean_dates(self, dfin: pd.DataFrame, tzname: str) -> pd.DataFrame:
        df = dfin.copy()
        for dt_col in self.dt_columns:
            df[dt_col] = pd.to_datetime(
                df[dt_col], format="%d-%m-%Y %H:%M:%S", errors="coerce"
            ).dt.tz_localize(tzname)
        return df

    def clean_column_names(self, dfin: pd.DataFrame):
        df = dfin.rename(columns=self.column_mapper)
        renamed_columns = []
        for i, col in enumerate(df.columns):
            if isinstance(col, str):
                if col[0].isdigit():
                    col = "unhandled_" + str(col)
            elif isinstance(col, (int, float)):
                col = "unhandled_" + str(col)
            elif isinstance(col, datetime.datetime):
                col = col.strftime("%b-%y")
            else:
                lg.error(f"{type(col)=}, {col=}")
                raise ValueError("Unexpected type in column name")
            cleaned_col = convert_to_snake_case(str(col))
            if cleaned_col:
                if cleaned_col not in renamed_columns:
                    renamed_columns.append(cleaned_col)
                else:
                    renamed_columns.append(f"{cleaned_col}_{i}")
            else:
                renamed_columns.append(f"unnamed_{i}")
        df.columns = renamed_columns
        return df

    def clean_data(self):
        raise NotImplementedError()

    def convert_df_to_dict_list(
        self, df: pd.DataFrame, delete_empty: bool = True
    ) -> list[dict]:
        datalist = []

        lg.info(f"Processing {df.shape=} to list[dict] ... ")
        for row in df.itertuples():
            # Create a copy of the dictionary representation of the row
            dr = row._asdict()

            # Clean the dictionary by removing keys with NaN/NaT values
            keys_to_delete = [
                row._fields[0],
            ]
            # Index 0 is the 'Index' column, which should be ignored in iteration
            for j, v in enumerate(row[1:], start=1):
                if pd.isna(v):
                    keys_to_delete.append(row._fields[j])
                if delete_empty:
                    # Remove keys with empty strings or NaT values
                    if isinstance(v, pd.Timestamp) and v == pd.NaT:
                        keys_to_delete.append(row._fields[j])
                    elif isinstance(v, str) and not v.strip():
                        keys_to_delete.append(row._fields[j])

            for key in keys_to_delete:
                del dr[key]
            # Compute the unique hash for the *cleaned* dictionary
            dr = self.append_data_hash(dr)
            datalist.append(dr)

        lg.info(f" Done -> {len(datalist)=}")
        return datalist

    def append_data_hash(self, data: dict) -> dict:
        """
        Computes a unique hash given dict (each row in the DataFrame).
        Adds a new column 'data_hash' with the computed hash values.
        """
        _hash = compute_row_hash(data)
        data["data_hash"] = _hash
        data["data_hash_dt"] = get_time_now()
        return data

    @abstractmethod
    def run(self):
        """Orchestration layer"""
        raise NotImplementedError()
