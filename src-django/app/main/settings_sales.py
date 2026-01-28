import os
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv

load_dotenv()


class SalesControllerConfig:
    INPUT_DIRNAME_SALES = "jetforge_inputs_sales/"
    SALES_INPUT_ALLOWED_EXT = ("",)
    SALES_FIELD_PARSERS = [
        "fct_input_month",
        "engine_output_forecast_month",
        "induction_month_stea",
        "engine_status",
    ]
    SALES_COLUMN_TO_ENGINE_DB_MAP: Dict[str, str] = {
        "uuid": "sales_forecast_uuid",
        "esn": "esn",
        "customer": "customer",
        "engine_type": "engine_model",
        "program_type": "shop_visit_scope",
        "fct_input_month": "fct_input_date",
        "actual_input_received_date": "input_date",
        "actual_induction_date": "induction_date",
        "facility": "facility",
        "certainty_of_engine_input": "certainty_of_engine_input",
        "engine_status": "status",
    }
    SALES_HOMEPAGE_DISPLAY_MODE = os.environ.get(
        "SALES_HOMEPAGE_DISPLAY_MODE", "unique_name"
    )  # ["unique_name", "unique_date"]
    MGDB_COLLECTION = "input_raw_dw_sales"
    MGDB_WINDOW_YEARS: int = 5
    MGDB_COLLECTION_ESN_LIST: str = "dim_esn_list"

    DEFAULTS_EXCEL_PARSER_CFM: Dict[str, Any] = {
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
    }

    DEFAULTS_EXCEL_PARSER_LEAP: Dict[str, Any] = {
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
    }

    def __init__(self, media_root: str):
        self.INPUT_DIRPATH_SALES = Path(media_root) / self.INPUT_DIRNAME_SALES
        self.INPUT_DIRPATH_SALES.mkdir(parents=True, exist_ok=True)
