import os
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

load_dotenv()


class OpsControllerConfig:
    INPUT_DIRNAME_OPS = "jetforge_inputs_ops/"
    OPS_INPUT_ALLOWED_EXT = ("",)
    OPS_PRODUCTION_HEADER_KEYS = ["UUID", "ESN"]
    OPS_FIELD_PARSERS = [
        # Date fields
        "engine_input_date",
        "induction",
        "gate_1a_completed",
        "gate_1b_completed",
        "gate_1_completed",
        "gate_2_kit_date",
        "gate_3a_start",
        "gate_3b_start_test_date_rigging",
        "g3_start",
        "test_date_rigging",
        "pass_test_date",
        "pack_ready_date",
        "shipment_date",
        "delivered_date_customer",
        # String fields
        "job_number",
        "esn",
        "uuid",
        "module_sn",
        "customer",
        "engine_model",
        "shop_visit_scope",
        "operator",
        "remarks",
        # Status fields
        "status",
        # Integer fields
        "gate_1_tat",
        "gross_tat",
        "net_tat",
        "key_issues_impacting_tat",
        "tat_from_induction_to_pass_test",
        "g3a_gross_tat",
        "g3b_gross_tat",
        "engine_build_to_pack_and_ready",
        "engine_pass_test_to_pack_and_ready",
    ]
    OPS_COLUMN_TO_ENGINE_DB_MAP: Dict[str, str] = {
        # String fields
        "uuid": "sales_forecast_uuid",
        "esn": "esn",
        "customer": "customer",
        "module_sn": "module_sn",
        "engine_model": "engine_model",
        "shop_visit_scope": "shop_visit_scope",
        "job_number": "job_number",
        "operator": "operator",
        "status": "status",
        "remarks": "master_remarks",
        # Date fields
        "engine_input_date": "input_date",
        "induction": "induction_date",
        "gate_1a_completed": "g1a_completion_date",
        "gate_1b_completed": "g1_completion_date_actual",
        "gate_1_completed": "g1_completion_date_actual",
        "gate_2_kit_date": "gate_2_kit_date",
        "gate_3a_start": "gate_3a_start",
        "g3_start": "gate_3a_start",
        "gate_3b_start_test_date_rigging": "test_date_rigging",
        "test_date_rigging": "test_date_rigging",
        "pass_test_date": "pass_test_date_actual",
        "pack_ready_date": "pack_ready_date_actual",
        "shipment_date": "shipment_date",
        "delivered_date_customer": "delivered_date_at_customer",
        # Integer fields
        "gate_1_tat": "gate_1_tat",
        "gross_tat": "gross_tat",
        "net_tat": "net_tat",
        "key_issues_impacting_tat": "key_issues_impacting_tat",
        "tat_from_induction_to_pass_test": "induction_to_pass_test_tat",
        "g3a_gross_tat": "g_3a_gross_tat_leap",
        "g3b_gross_tat": "g_3b_gross_tat_leap",
        "engine_build_to_pack_and_reay": "engine_build_to_pack_ready_tat",
        "engine_pass_test_to_pack_and_ready": "packing_tat",
    }
    OPS_HOMEPAGE_DISPLAY_MODE = os.environ.get(
        "OPS_HOMEPAGE_DISPLAY_MODE", "unique_name"
    )  # ["unique_name", "unique_date"]
    MGDB_COLLECTION = "input_raw_dw_ops"
    MGDB_WINDOW_YEARS: int = 5
    MGDB_COLLECTION_ESN_LIST: str = "dim_esn_list"

    def __init__(self, media_root: str):
        self.INPUT_DIRPATH_OPS = Path(media_root) / self.INPUT_DIRNAME_OPS
        self.INPUT_DIRPATH_OPS.mkdir(parents=True, exist_ok=True)
