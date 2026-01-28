import logging
import os
import re
from typing import Any, Dict, List, Optional

import pytz
from customers import models as customers_models
from django.conf import settings
from django.contrib.auth import get_user_model
from dotenv import load_dotenv
from engines import models as engines_models
from joborders import models as joborders_models
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
MGDB_COLL_INPUT_LEADINGORDERS = "input_raw_dw_leadingorders"


def create_slug(text: str) -> str:
    """
    Converts a string of words into a URL/data-friendly slug.

    Rules:
    - Only lowercase.
    - Only alphanumeric, hyphens (-), and underscores (_) are allowed.
    - Other characters are converted to hyphens.
    """
    # 1. Convert to lowercase
    text = text.lower()

    # 2. Replace all characters that are NOT a-z, 0-9, hyphen, or underscore with a hyphen.
    # This handles spaces, commas, periods, parentheses, etc.
    # The [^...] pattern matches any character NOT in the set. The '+' ensures
    # multiple non-allowed characters in a row are replaced by a single hyphen.
    # Note: Underscore is included as an allowed character per your request.
    text = re.sub(r"[^a-z0-9_-]+", "-", text)

    # 3. Clean up multiple hyphens (e.g., "---" -> "-")
    text = re.sub(r"-+", "-", text)

    # 4. Remove leading/trailing hyphens or underscores
    text = text.strip("-_")

    return text


def get_engine_series(model_name: str) -> Optional[str]:
    """
    Parses an engine model string to determine its series (CFM56 or LEAP).

    Args:
        model_name: The string representing the engine model (e.g., 'CFM56-7B').

    Returns:
        The recognized series string ('CFM56', 'LEAP'), or 'UNKNOWN'.
    """
    # Normalize the input by converting to uppercase to handle case variations
    model_name_upper = model_name.upper()

    if model_name_upper.startswith("CFM56"):
        return "CFM56"

    # Check for LEAP, handling both 'LEAP' and 'LEAP-' prefixes
    elif model_name_upper.startswith("LEAP"):
        return "LEAP"

    return None


def get_engine_make(series: str) -> Optional[str]:
    _series = series.upper()
    if _series.startswith("CFM56") or _series.startswith("LEAP"):
        return "CFMI"
    return None


def clean_engine_model(v: str) -> Optional[str]:
    if not v:
        return None
    model = v.strip().upper()
    match model:
        case "CFM56-7B" | "CFM56-5B":
            return model
        case "CFM56" | "LEAP":
            raise ValueError(f"{v=} is an invalid engine model")
        case "CFM56 7B" | "CFM56_7B" | "CFM56/7B" | "7B" | "CFM-7B":
            return "CFM56-7B"
        case "CFM56 5B" | "CFM56_5B" | "CFM56/5B" | "5B" | "CFM-5B":
            return "CFM56-5B"
        case _:
            return model


class Transformer:
    """
    Transformer class for processing leading orders data.
    """

    def __init__(self, db):
        self.db = db
        # Ensure admin user exists for tracking
        self.admin_user, _ = User.objects.get_or_create(
            username=settings.DJANGO_SUPERUSER_ADMIN
        )

    def connect_to_db(self) -> None:
        self.db.connect()
        self.db.connect_to_collection()

    def fetch_all_data(self) -> List[Dict[str, Any]]:
        return self.db.query_data()

    def load_referenceordermodel(
        self, data: Dict[str, Any]
    ) -> Optional[joborders_models.ReferenceOrderModel]:
        """Load a ReferenceOrderModel instance from the provided data."""
        ro_number = data.get("ref_order_no", "").strip()
        ro_customer = data.get("ref_order_customer", "").strip()
        if not ro_number and not ro_customer:
            return None

        slug_ro_number = create_slug(ro_number)
        slug_ro_customer = create_slug(ro_customer)

        # Generate deterministic UUID for uniqueness
        ro_uuid = f"{slug_ro_number}::{slug_ro_customer}"

        obj, is_created = joborders_models.ReferenceOrderModel.objects.get_or_create(
            uuid=ro_uuid,
        )

        data_hash = data.get("data_hash", None)
        has_changes = False
        log_txt = ""

        if is_created:
            log_txt = f"Created ReferenceOrder({ro_number=})."
            if ro_number:
                obj.ro_number = ro_number
            if ro_customer:
                obj.ro_customer_name = ro_customer

            obj.user_created = self.admin_user
            has_changes = True
        else:
            # Update Check
            if ro_number and obj.ro_number != ro_number:
                obj.ro_number = ro_number
                obj.changelog.append(
                    {
                        "msg": f"Updated number to {ro_number} via {data_hash}",
                        "dt": get_datetime_str(),
                    }
                )
                has_changes = True

            if ro_customer and obj.ro_customer_name != ro_customer:
                obj.ro_customer_name = ro_customer
                obj.changelog.append(
                    {
                        "msg": f"Updated customer to {ro_customer} via {data_hash}",
                        "dt": get_datetime_str(),
                    }
                )
                has_changes = True

        if has_changes:
            if log_txt:
                obj.changelog.append(
                    {"msg": f"{log_txt} {data_hash=}", "dt": get_datetime_str()}
                )
            obj.user_modified = self.admin_user
            obj.save()

        return obj

    def load_enginemakemodel(
        self, data: Dict[str, Any]
    ) -> Optional[engines_models.EngineMakeModel]:
        """Load an EngineMakeModel instance from the provided data."""

        # Input: "CFM56-7B" or "LEAP-1A"
        model_name = data.get("engine_model").strip()
        model_name = clean_engine_model(model_name)
        if not model_name:
            return None
        submodel = data.get("engine_submodel", "undefined").strip()

        slug_model_name = create_slug(model_name)
        slug_submodel = create_slug(submodel)
        uuid = f"{slug_model_name}::{slug_submodel}"

        series = data.get("engine_series", "").strip()
        if not series:
            series = get_engine_series(model_name)

        make = get_engine_make(series) if series else None

        obj, is_created = engines_models.EngineMakeModel.objects.get_or_create(
            uuid=uuid
        )
        if is_created:
            obj.changelog.append(
                {"msg": f"Created EngineMake({uuid=})", "dt": get_datetime_str()}
            )
            if model_name:
                obj.model = model_name
            if submodel:
                obj.submodel = submodel
            if series:
                obj.series = series
            if make:
                obj.make = make

            obj.user_created = self.admin_user
            obj.user_modified = self.admin_user
            obj.save()
        else:
            # Engine Make rarely changes
            # We will skip the update logic (if any)
            # POTENTIAL_BUG
            pass

        return obj

    # ---------------------------------------------------------
    # 3. Engine Instance Loader
    # ---------------------------------------------------------
    def load_engineinstancemodel(
        self, data: Dict[str, Any]
    ) -> Optional[engines_models.EngineInstanceModel]:
        esn = data.get("engine_sn")
        if not esn:
            return None

        # Dependency: We must have a Make to create an Instance
        make_obj = self.load_enginemakemodel(data)
        if not make_obj:
            # Cannot create instance without a make (Foreign Key constraint)
            return None

        # Try to get existing instance by ESN (assuming ESN is unique enough for lookup logic)
        # Note: Model definition doesn't strictly force ESN unique, but logically it is.
        # We use filter().first() or get_or_create depending on confidence in data.
        obj = engines_models.EngineInstanceModel.objects.filter(esn=esn).first()
        is_created = False

        if not obj:
            obj = engines_models.EngineInstanceModel(esn=esn, make=make_obj)
            is_created = True

        data_hash = data.get("data_hash", None)
        has_changes = False

        # Fields to check
        thrust = data.get("engine_thrust_rating")

        if is_created:
            if thrust:
                obj.thrust_rating = thrust

            obj.changelog.append(
                {
                    "msg": f"Created Engine {esn} (Make: {make_obj.model})",
                    "dt": get_datetime_str(),
                }
            )
            obj.user_created = self.admin_user
            has_changes = True
        else:
            # Update Check
            if thrust and obj.thrust_rating != thrust:
                obj.thrust_rating = thrust
                obj.changelog.append(
                    {
                        "msg": f"Updated thrust to {thrust} via {data_hash}",
                        "dt": get_datetime_str(),
                    }
                )
                has_changes = True

            # Edge Case: If Make changed in source? Usually rare.
            if obj.make != make_obj:
                obj.make = make_obj
                has_changes = True

        if has_changes:
            obj.user_modified = self.admin_user
            obj.save()

        return obj

    # ---------------------------------------------------------
    # 4. Customer Loader (Reviewed & Refined)
    # ---------------------------------------------------------
    def load_enginecustomermodel(
        self, data: Dict[str, Any]
    ) -> customers_models.EngineCustomerModel:
        """
        Refined logic:
        1. Fixes 'strip' usage.
        2. Fixes user assignment logic (inside save blocks).
        3. Ensures 'code' doesn't exceed max_length.
        """
        log_txt = ""

        name = data.get("customer_name", "").strip()
        name_short = data.get("customer_name_short", "").strip()

        # Generate Slug
        s_name = create_slug(name)
        s_short = create_slug(name_short)

        raw_uuid = f"{s_short}::{s_name}"
        if raw_uuid == "::":  # Empty
            return None

        # Safety truncate to model's max_length (256 in updated model, used to be 64)
        customer_uuid = raw_uuid[:256]

        obj, is_created = customers_models.EngineCustomerModel.objects.get_or_create(
            code=customer_uuid
        )

        data_hash = data.get("data_hash", None)
        has_changes = False

        if is_created:
            log_txt = f"Created Customer ({customer_uuid})."

            if name:
                obj.name = name
            elif not obj.name:
                obj.name = customer_uuid  # Fallback to avoid blank name

            if name_short:
                obj.name_short = name_short

            obj.changelog.append(
                {"msg": f"{log_txt} Hash={data_hash}", "dt": get_datetime_str()}
            )

            obj.user_created = self.admin_user
            has_changes = True
        else:
            # Update Logic
            if name and obj.name != name:
                obj.name = name
                obj.changelog.append(
                    {"msg": f"Updated name to {name}", "dt": get_datetime_str()}
                )
                has_changes = True

            if name_short and obj.name_short != name_short:
                obj.name_short = name_short
                obj.changelog.append(
                    {
                        "msg": f"Updated short_name to {name_short}",
                        "dt": get_datetime_str(),
                    }
                )
                has_changes = True

        if has_changes:
            obj.user_modified = self.admin_user
            obj.save()

        return obj

    # ---------------------------------------------------------
    # 5. Leading Order Loader (Integrates all above)
    # ---------------------------------------------------------
    def load_leadingordermodel(
        self, data: Dict[str, Any]
    ) -> joborders_models.ReferenceOrderModel:
        """
        Load a LeadingOrderModel.
        Now resolves Foreign Keys for Engine, Customer, and ReferenceOrder.
        """
        lo_number = data.get("service_order_no")
        if not lo_number:
            return None  # Cannot exist without LO number

        esn = data.get("engine_sn", None)

        # 1. Resolve Dependencies
        customer_obj = self.load_enginecustomermodel(data)
        ref_order_obj = self.load_referenceordermodel(data)

        # 2. Get or Create Main Object
        obj, is_created = joborders_models.LeadingOrderModel.objects.get_or_create(
            lo_number=lo_number
        )

        data_hash = data.get("data_hash", None)
        has_changes = False

        # 3. Prepare values for comparison/update
        input_reason = data.get("reason_for_input")
        input_job_type = (
            data.get("job_type", "").lower() if data.get("job_type") else None
        )
        input_status = data.get("leading_order_status_name")

        dt_engine_created = data.get("engine_created_date", None)
        dt_engine_stage = data.get("engine_stage_date", None)
        dt_engine_output = data.get("engine_output_date", None)
        # MongoDB datetime are timezone-aware in UTC
        # We will use utc_tz make tz-aware for django orm
        utc_tz = pytz.timezone("UTC")

        # -----------------------------------------------------
        # Creation Logic
        # -----------------------------------------------------
        if is_created:
            log_msg = f"Created LO {lo_number}."

            engine_obj = self.load_engineinstancemodel(data)

            # Set Scalars
            if input_reason:
                obj.reason_for_input = input_reason
            if input_job_type:
                obj.job_type = input_job_type
            if input_status:
                obj.status = input_status
            if dt_engine_created:
                obj.dt_engine_created = dt_engine_created
            if dt_engine_stage:
                obj.dt_engine_stage = dt_engine_stage
            if dt_engine_output:
                obj.dt_engine_output = dt_engine_output

            # Set Relations
            if customer_obj:
                obj.customer = customer_obj
            if engine_obj:
                obj.engine = engine_obj
            if ref_order_obj:
                obj.ref_order = ref_order_obj

            obj.changelog.append(
                {"msg": f"{log_msg} Hash={data_hash}", "dt": get_datetime_str()}
            )
            obj.user_created = self.admin_user
            has_changes = True

        # -----------------------------------------------------
        # Update Logic
        # -----------------------------------------------------
        else:
            # Check Scalars
            if input_reason and obj.reason_for_input != input_reason:
                obj.reason_for_input = input_reason
                has_changes = True

            if input_job_type and obj.job_type != input_job_type:
                obj.job_type = input_job_type
                has_changes = True

            if input_status and obj.status != input_status:
                obj.status = input_status
                has_changes = True

            if dt_engine_created and obj.dt_engine_created != dt_engine_created:
                obj.dt_engine_created = dt_engine_created.replace(tzinfo=utc_tz)
                has_changes = True

            if dt_engine_stage and obj.dt_engine_stage != dt_engine_stage:
                obj.dt_engine_stage = dt_engine_stage.replace(tzinfo=utc_tz)
                has_changes = True

            if dt_engine_output and obj.dt_engine_output != dt_engine_output:
                obj.dt_engine_output = dt_engine_output.replace(tzinfo=utc_tz)
                has_changes = True

            # Check Relations (Foreign Keys)
            if customer_obj and obj.customer != customer_obj:
                obj.customer = customer_obj
                has_changes = True

            if esn:
                if obj.engine.esn != esn:
                    obj.engine.esn = esn
                    obj.engine.changelog.append(
                        {
                            "msg": f"Updated esn via leadingordermodel({obj.pk})",
                            "dt": get_datetime_str(),
                        }
                    )
                    obj.engine.save()
                    obj.changelog.append(
                        {
                            "msg": f"Updated engines.esn via Hash={data_hash}",
                            "dt": get_datetime_str(),
                        }
                    )
                    has_changes = True

            if ref_order_obj and obj.ref_order != ref_order_obj:
                obj.ref_order = ref_order_obj
                has_changes = True

            if has_changes:
                obj.changelog.append(
                    {
                        "msg": f"Updated fields via Hash={data_hash}",
                        "dt": get_datetime_str(),
                    }
                )

        # 4. Save
        if has_changes:
            obj.user_modified = self.admin_user
            obj.save()

        return obj


def transform() -> int:
    lg.info("Running transformation process...")

    trf = Transformer(
        db=MongoDbHelper(
            connection_str=MGDB_CONNX,
            collection_name=MGDB_COLL_INPUT_LEADINGORDERS,
            batch_size=1000,
        )
    )
    trf.connect_to_db()

    datalist = trf.fetch_all_data()
    total = len(datalist)

    for i, d in enumerate(datalist, 1):
        obj = trf.load_leadingordermodel(d)
        lg.info(f"[{i}/{total}] Loaded LeadingOrderModel: {obj}")

    return i


if __name__ == "__main__":
    transform()
