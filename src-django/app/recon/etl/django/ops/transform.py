import logging
import os
from typing import Any, Dict, List

import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from dotenv import load_dotenv
from operations import models as ops_models
from main.utils import get_datetime_str, parse_mongo_uri
from recon.etl.core.db import MongoDbHelper

load_dotenv()
User = get_user_model()
lg = logging.getLogger("django")

MGDB_CONNECTION_STR = os.getenv(
    "MGDB_CONNECTION_STR", "mongodb://localhost:27017/default_db"
)
MGDB_CONNX = settings.MGDB_CONNECTION_STR
MGDB = parse_mongo_uri(MGDB_CONNX)
MGDB_COLL_INPUT_SALES = "input_raw_dw_ops"

utc_tz = pytz.timezone("UTC")


class Transformer:
    """
    Transformer class for processing ops file raw data.
    """

    def __init__(self, db):
        self.db = db
        # Ensure admin user exists for tracking
        self.admin_user, _ = User.objects.get_or_create(
            username=settings.DJANGO_SUPERUSER_ADMIN
        )

    def _sanitize_str(self, value):
        """
        Helper for cleaning string data - strip, lower and handle None.
        """
        if value is None:
            return None
        if isinstance(value, str):
            return value.strip().upper()
        return value

    def _clean_esn(self, value: str):
        """
        Helper for cleaning esn data, especially for handling LEAP modules.
        """
        stripped = value.replace(" ", "")
        split = stripped.split("SM")
        return split
    
    def _clean_job_number(self, value: str):
        """
        Helper for cleaning job number data.
        """
        if value is None:
            return None
        if isinstance(value, str):
            if "." in value:
                value = value.split(".")[0]  # Remove any decimal part
            return value.strip().upper()
        return value

    def connect_to_db(self) -> None:
        self.db.connect()
        self.db.connect_to_collection()

    def fetch_all_data(self) -> List[Dict[str, Any]]:
        return self.db.query_data()

    def load_opsmodel(self, data: Dict[str, Any]) -> ops_models.OrderOperationsModel:
        """
        Load an OrderOperationsModel.
        """
        sales_uuid = data.get("uuid")
        if not sales_uuid:
            return None  # Cannot exist without uuid

        # 1. Determine Actual vs Forecast values upfront
        engine_status = self._sanitize_str(data.get("status"))

        split_esn = self._clean_esn(self._sanitize_str(data.get("esn")))
        esn = split_esn[0]

        field_map = {
            "esn": esn,
            "engine_model": self._sanitize_str(data.get("engine_model")),
            "customer": self._sanitize_str(data.get("customer")),
            "operator": self._sanitize_str(data.get("operator")),
            "job_number": self._clean_job_number(data.get("job_number")),
            "shop_visit_scope": self._sanitize_str(data.get("shop_visit_scope")),
            "status": engine_status,
            "key_issues_impacting_tat": self._sanitize_str(data.get("key_issues_impacting_tat")),
            "remarks": self._sanitize_str(data.get("remarks")),
        }

        input_date = (
            data.get("engine_input_date") if data.get("engine_input_date") else None
        )
        induction_date = data.get("induction") if data.get("induction") else None

        gate_1_date = (
            data.get("gate_1_completed") if data.get("gate_1_completed") else None
        )
        gate_1a_date = (
            data.get("gate_1a_completed") if data.get("gate_1a_completed") else None
        )
        gate_1b_date = (
            data.get("gate_1b_completed") if data.get("gate_1b_completed") else None
        )
        gate_2_date = (
            data.get("gate_2_kit_date") if data.get("gate_2_kit_date") else None
        )
        rigging_date = (
            data.get("test_date_rigging") if data.get("test_date_rigging") else None
        )
        gate_3_date = data.get("g3_start") if data.get("g3_start") else None

        gate_3a_date = data.get("gate_3a_start") if data.get("gate_3a_start") else None

        gate_3b_date = (
            data.get("gate_3b_start_test_date_rigging")
            if data.get("gate_3b_start_test_date_rigging")
            else None
        )
        pass_test_date = (
            data.get("pass_test_date") if data.get("pass_test_date") else None
        )
        pack_ready_date = (
            data.get("pack_ready_date") if data.get("pack_ready_date") else None
        )
        shipment_date = data.get("shipment_date") if data.get("shipment_date") else None

        # Handle the conditional field suffixes
        if engine_status == "COMPLETED":
            date_field_suffix = "_actual"
        else:
            date_field_suffix = "_target"

        field_map.update(
            {
                "dt_input" + date_field_suffix: input_date.replace(tzinfo=utc_tz)
                if input_date
                else None,
                "dt_induction" + date_field_suffix: induction_date.replace(
                    tzinfo=utc_tz
                )
                if induction_date
                else None,
                "dt_gate_1" + date_field_suffix: gate_1_date.replace(tzinfo=utc_tz)
                if gate_1_date
                else None,
                "dt_gate_1a" + date_field_suffix: gate_1a_date.replace(tzinfo=utc_tz)
                if gate_1a_date
                else None,
                "dt_gate_1b" + date_field_suffix: gate_1b_date.replace(tzinfo=utc_tz)
                if gate_1b_date
                else None,
                "dt_gate_2_kitting" + date_field_suffix: gate_2_date.replace(
                    tzinfo=utc_tz
                )
                if gate_2_date
                else None,
                "dt_rigging" + date_field_suffix: rigging_date.replace(tzinfo=utc_tz)
                if rigging_date
                else None,
                "dt_gate_3" + date_field_suffix: gate_3_date.replace(tzinfo=utc_tz)
                if gate_3_date
                else None,
                "dt_gate_3a" + date_field_suffix: gate_3a_date.replace(tzinfo=utc_tz)
                if gate_3a_date
                else None,
                "dt_gate_3b" + date_field_suffix: gate_3b_date.replace(tzinfo=utc_tz)
                if gate_3b_date
                else None,
                "dt_pass_test" + date_field_suffix: pass_test_date.replace(
                    tzinfo=utc_tz
                )
                if pass_test_date
                else None,
                "dt_pack_ready" + date_field_suffix: pack_ready_date.replace(
                    tzinfo=utc_tz
                )
                if pack_ready_date
                else None,
                "dt_shipment" + date_field_suffix: shipment_date.replace(tzinfo=utc_tz)
                if shipment_date
                else None,
            }
        )

        # 2. Get or Create Main Object
        obj, is_created = ops_models.OrderOperationsModel.objects.get_or_create(
            sales_uuid=sales_uuid
        )
        has_changes = False
        data_hash = data.get("data_hash", None)

        # 3. Dynamic Assignment & Comparison
        for field, value in field_map.items():
            lg.info(f"{field=}")
            if value is not None and getattr(obj, field) != value:
                setattr(obj, field, value)
                has_changes = True

        # 4. Handle logging and saving
        if is_created or has_changes:
            msg = f"{'Created' if is_created else 'Updated'} sales uuid {sales_uuid}. Hash={data_hash}"
            obj.changelog.append({"msg": msg, "dt": get_datetime_str()})

            if is_created:
                obj.user_created = self.admin_user
            obj.user_modified = self.admin_user
            obj.save()

        return obj


def transform() -> int:
    lg.info("Running transformation process...")

    trf = Transformer(
        db=MongoDbHelper(
            connection_str=MGDB_CONNX,
            collection_name=MGDB_COLL_INPUT_SALES,
            batch_size=1000,
        )
    )
    trf.connect_to_db()

    datalist = trf.fetch_all_data()
    total = len(datalist)

    for i, d in enumerate(datalist, 1):
        ops_obj = trf.load_opsmodel(d)
        lg.info(f"[{i}/{total}] Loaded OpsModel: {ops_obj}")

    return i


if __name__ == "__main__":
    transform()
