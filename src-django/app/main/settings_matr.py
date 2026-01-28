import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class MaterialsControllerConfig:
    INPUT_DIRNAME_ZMMR3010 = "jetforge_inputs_zmmr3010/"
    OUTPUT_DIRNAME_ZMMR3010 = "jetforge_outputs_zmmr3010/"
    INPUT_DIRNAME_LEADINGORDER = "jetforge_inputs_leadingorder/"
    OUTPUT_DIRNAME_LEADINGORDER = "jetforge_outputs_leadingorder/"
    MATR_INPUT_ALLOWED_EXT = ("",)
    MATR_OUTPUT_COLUMNS_MAPPING = {
        "Part Number": "part_no",
        "Description": "descr",
        "Sort Strin": "sort_str",
        "NOEA": "qty_engine_job_requiring",
        "TQS": "qty_total_shortage",
        "DUES IN": "dues_in",
        "FV": "FV",
        "FVB": "FVB",
        "GCDR": "GCDR",
        "GH": "GH",
        "GHA": "GHA",
        "GHN": "GHN",
        "GHP": "GHP",
        "GHR": "GHR",
        "GHRN": "GHRN",
        "GLS": "GLS",
        "GPS": "GPS",
        "GR": "GR",
        "GSV": "GSV",
        "GV": "GV",
        "GVA": "GVA",
        "GVJT": "GVJT",
        "GVMN": "GVMN",
        "GVNS": "GVNS",
        "GVR": "GVR",
        "esn": "esn",
        "engine_qty_shortage": "qty_shortage_engine",
    }
    MATR_HOMEPAGE_DISPLAY_MODE = os.environ.get(
        "MATR_HOMEPAGE_DISPLAY_MODE", "unique_name"
    )  # ["unique_name", "unique_date"]
    MATR_OUTPUT_KW_PIECEJOB = {"unnamed_col0000": "piece_job"}
    MGDB_COLLECTION = "input_raw_zmmr3010"
    MGDB_WINDOW_YEARS: int = 5
    MGDB_COLLECTION_ESN_LIST: str = "dim_esn_list"

    def __init__(self, media_root: str):
        self.INPUT_DIRPATH_ZMMR3010 = Path(media_root) / self.INPUT_DIRNAME_ZMMR3010
        self.INPUT_DIRPATH_ZMMR3010.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIRPATH_ZMMR3010 = Path(media_root) / self.OUTPUT_DIRNAME_ZMMR3010
        self.OUTPUT_DIRPATH_ZMMR3010.mkdir(parents=True, exist_ok=True)
        self.INPUT_DIRPATH_LEADINGORDER = (
            Path(media_root) / self.INPUT_DIRNAME_LEADINGORDER
        )
        self.INPUT_DIRPATH_LEADINGORDER.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIRPATH_LEADINGORDER = (
            Path(media_root) / self.OUTPUT_DIRNAME_LEADINGORDER
        )
        self.OUTPUT_DIRPATH_LEADINGORDER.mkdir(parents=True, exist_ok=True)
        self.validate_config_values()

    def validate_config_values(self) -> None:
        if len(self.MATR_OUTPUT_KW_PIECEJOB) != 1:
            raise ValueError(f"{self.MATR_OUTPUT_KW_PIECEJOB=}; only accept ==1")
