import logging
import os
from typing import Any, Dict, List

import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from dotenv import load_dotenv
from sales import models as sales_models
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
MGDB_COLL_INPUT_SALES = "input_raw_dw_sales"

utc_tz = pytz.timezone("UTC")


class Transformer:
    """
    Transformer class for processing sales file raw data.
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

    def connect_to_db(self) -> None:
        self.db.connect()
        self.db.connect_to_collection()

    def fetch_all_data(self) -> List[Dict[str, Any]]:
        return self.db.query_data()

    def load_salesmodel(self, data: Dict[str, Any]) -> sales_models.SalesModel:
        """
        Load a SalesModel.
        """
        uuid = data.get("uuid")
        if not uuid:
            return None  # Cannot exist without uuid

        # 1. Determine Actual vs Forecast values upfront
        engine_status = self._sanitize_str(data.get("engine_status", ""))
        val = data.get("actual_fct_sales_value") or data.get("fct_sales_value")
        cost = data.get("actual_fct_cost") or data.get("fct_cost")
        gp = data.get("actual_fct_gp") or data.get("fct_gp")

        # 2. Map data to model field names
        # Format: { model_field_name: sanitized_value }
        field_map = {
            "salesperson": self._sanitize_str(data.get("salesperson")),
            "program_type": self._sanitize_str(data.get("program_type")),
            "est_sales_us": data.get("est_sales_us"),
            "bid_status": self._sanitize_str(data.get("bid_status")),
            "approved_gp_during_bid": data.get("approved_gp_during_bid"),
            "prelim_cost_day_35_review_conducted_y_n": data.get(
                "prelim_cost_day_35_review_conducted_y_n"
            ),
            "final_cost_1_day_before_testing_review_conducted_y_n": data.get(
                "final_cost_1_day_before_testing_review_conducted_y_n"
            ),
            "sales_recognition_status": self._sanitize_str(
                data.get("sales_recognition_status")
            ),
            "gp_percent": data.get("gp"),
            "poc_effect": self._sanitize_str(data.get("poc_effect")),
            "poc_cost_mark_up": data.get("poc_cost_mark_up"),
            "poc_sales_b_f": data.get("poc_sales_b_f"),
            "poc_cost_b_f": data.get("poc_cost_b_f"),
            "poc": data.get("poc"),
        }

        # Handle the conditional fields
        if engine_status == "COMPLETED":
            field_map.update(
                {"actual_sales_value": val, "actual_cost": cost, "actual_gp": gp}
            )
        else:
            field_map.update({"fct_sales_value": val, "fct_cost": cost, "fct_gp": gp})

        # 3. Get or Create Main Object
        obj, is_created = sales_models.SalesModel.objects.get_or_create(uuid=uuid)
        has_changes = False
        data_hash = data.get("data_hash", None)

        # 4. Dynamic Assignment & Comparison
        for field, value in field_map.items():
            if value is not None and getattr(obj, field) != value:
                setattr(obj, field, value)
                has_changes = True

        # 5. Handle logging and saving
        if is_created or has_changes:
            msg = f"{'Created' if is_created else 'Updated'} sales uuid {uuid}. Hash={data_hash}"
            obj.changelog.append({"msg": msg, "dt": get_datetime_str()})

            if is_created:
                obj.user_created = self.admin_user
            obj.user_modified = self.admin_user
            obj.save()

        return obj

    def load_opsmodel(self, data: Dict[str, Any]) -> ops_models.OrderOperationsModel:
        """
        Load an OrderOperationsModel.
        """
        sales_uuid = data.get("uuid")
        if not sales_uuid:
            return None  # Cannot exist without uuid

        # 1. Determine Actual vs Forecast values upfront
        engine_status = self._sanitize_str(data.get("engine_status", ""))

        split_esn = self._clean_esn(self._sanitize_str(data.get("esn")))
        esn = split_esn[0]
        shop_visit_scope = self._sanitize_str(data.get("program_type"))
        if len(split_esn) > 1:
            shop_visit_scope = "SM" + split_esn[1]

        input_date = (
            data.get("actual_input_received_date")
            if data.get("actual_input_received_date")
            else None
        )
        induction_date = next(
            (v for k, v in data.items() if "actual_induction_date" in k and v), 
            None
        )
        shipment_date = (
            data.get("actual_output_date_shipment")
            if data.get("actual_output_date_shipment")
            else None
        )
        engine_output_forecast_month_see_note_for_lion_air = (
            data.get("engine_output_forecast_month_see_note_for_lion_air")
            if data.get("engine_output_forecast_month_see_note_for_lion_air")
            else None
        )

        field_map = {
            "esn": esn,
            "engine_type": self._sanitize_str(data.get("engine_type")),
            "customer": self._sanitize_str(data.get("customer")),
            "shop_visit_scope": shop_visit_scope,
            "status": engine_status,
            "facility": self._sanitize_str(data.get("facility")),
            "certainty_of_engine_input": self._sanitize_str(
                data.get("certainty_of_engine_input")
            ),
            "engine_output_forecast_month_see_note_for_lion_air": engine_output_forecast_month_see_note_for_lion_air.replace(
                tzinfo=utc_tz
            )
            if engine_output_forecast_month_see_note_for_lion_air
            else None,
        }

        # Handle the conditional fields
        if engine_status == "COMPLETED":
            field_map.update(
                {
                    "dt_input_actual": input_date.replace(tzinfo=utc_tz)
                    if input_date
                    else None,
                    "dt_induction_actual": induction_date.replace(tzinfo=utc_tz)
                    if induction_date
                    else None,
                    "dt_shipment_actual": shipment_date.replace(tzinfo=utc_tz)
                    if shipment_date
                    else None,
                }
            )
        else:
            field_map.update(
                {
                    "dt_input_target": input_date.replace(tzinfo=utc_tz)
                    if input_date
                    else None,
                    "dt_induction_target": induction_date.replace(tzinfo=utc_tz)
                    if induction_date
                    else None,
                    "dt_shipment_target": shipment_date.replace(tzinfo=utc_tz)
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
        sales_obj = trf.load_salesmodel(d)
        lg.info(f"[{i}/{total}] Loaded SalesModel: {sales_obj}")
        ops_obj = trf.load_opsmodel(d)
        lg.info(f"[{i}/{total}] Loaded OpsModel: {ops_obj}")

    return i


if __name__ == "__main__":
    transform()
