# etl/transform.py

import logging
import os
import re
from typing import Any, Dict, List, Optional

import pandas as pd
from creds import models as account_models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Model as DjangoModel
from engines import models as engine_models
from main.config import ConfigHelper
from main.utils import convert_to_snake_case
from recon import models as recon_models
from recon.etl.db import MongoDbHelper
from outhouse import models as outhouse_models

# Models are Django ORM (django-mongo-backend)

class SkipException(Exception):
    """Custom exception to skip processing of a document."""

    pass


logger = logging.getLogger("django")
cf = ConfigHelper()
config = cf.config


def parse_awb_data(raw_string: str) -> Optional[Dict[str, Optional[str]]]:
    """
    Parses a raw shipment string using the AWB_REGEX and structures the results.
    """

    # Regex Explanation:
    # 1. ^(?P<vendor>...): Starts by capturing the vendor name (Bollore, DHL, FEDEX, or Local).
    # 2. (?:...)?$: The entire awb/mawb/hawb section is wrapped in a non-capturing optional group (?:...)?
    #    and is anchored to the end of the string ($). This allows "Local" to match successfully.
    # 3. (?:mawb:\s*(?P<mawb>[\w-]+)...): The first alternative tries to match the complex mawb/hawb format.
    # 4. (?P<SingleAWB>[\d\s-]+): The second alternative matches a single number (used for DHL/FEDEX).
    #    It captures digits, spaces, and hyphens to be flexible with formatting.
    AWB_REGEX = re.compile(
        r"""
        ^
        (?P<vendor>
            Bollore\s+Logistics\s+Singapore
            |DHL
            |FEDEX
            |Local
        )
        (?:
            \s+ # Match one or more spaces after the vendor
            (?:
                # Complex Format (mawb/hawb)
                mawb:\s*(?P<mawb>[\w-]+)
                \s* # Optional whitespace/newline between mawb and hawb
                hawb:\s*(?P<hawb>[\w-]+)
            |
                # Simple Format (Single awb Number)
                (?P<SingleAWB>[\d\s-]+)
            )
        )?
        $
    """,
        re.VERBOSE | re.IGNORECASE | re.DOTALL,
    )  # Multi-line comments, case-insensitive, and dot matches newline

    match = AWB_REGEX.match(raw_string)

    # Initialize the results with default values (None)
    result = {
        "vendor": None,
        "awb": None,
        "mawb": None,
        "hawb": None,
    }

    if not match:
        raise ValueError(f"parse_awb_data() Could not parse: {raw_string}")

    # Extract all named groups from the match
    data = match.groupdict()

    # Clean up vendor name (e.g., remove excess whitespace) and assign
    vendor = data.get("vendor", "")
    if vendor:
        vendor = vendor.strip().lower()
    result["vendor"] = vendor

    # Assign mawb and hawb directly if they were captured
    # We strip and use `or None` to ensure empty strings become None
    mawb = data.get("mawb", "")
    if mawb:
        mawb = mawb.strip()
    result["mawb"] = mawb
    hawb = data.get("hawb", "")
    if hawb:
        hawb = hawb.strip()
    result["hawb"] = hawb

    # awb determination logic:
    # 1. If mawb exists, use it as the main awb.
    if result["mawb"]:
        result["awb"] = result["mawb"]
    # 2. If a simple awb number was captured, use that.
    elif data.get("SingleAWB"):
        # Clean up the single awb by removing internal spaces/newlines
        result["awb"] = re.sub(r"\s+", "", data["SingleAWB"]).strip()
    # 3. Otherwise, awb remains None.

    return result


def write_hash_to_transaction(obj: DjangoModel, doc: dict) -> DjangoModel:
    datahash = doc.get("data_hash", None)
    if not datahash:
        raise ValueError("Document must contain 'data_hash' field.")
    obj.data_from_hash = datahash
    obj.save()
    return obj


class OhSubconExcelDataTransformer:
    collection_name: str = "raw_subcon"
    column_mapper: dict = {
        "R/O NO": "ro_no",
        "Quote r'cd from Vdr on": "quote_rcv_from_vdr_on",
        "Quote approval r'cd from CS on": "quote_approval_rcv_from_cs_on",
    }
    dt_columns: list = [
        "date_kit_list_sent",
        "date_ci_provided",
        "arrive_vdr_date",
        "quote_rcv_from_vdr_on",
        "quote_submit_to_cs_on",
        "quote_approval_rcv_from_cs_on",
        "quote_approve_to_vdr_on",
        "esd",
        "part_arrived_st",
        "gr_date",
    ]

    def __init__(
        self,
        mongo_db: MongoDbHelper,
        collection_name: str = "raw_subcon",
    ):
        self.collection_name = collection_name
        self.db = mongo_db

    def iter_all(self):
        for doc in self.db.collection.find({}, {"_id": 0}):
            yield doc

    def register_update_record(
        self, datahash: str
    ) -> recon_models.ExcelRowRecordsModel:
        """Register or update ExcelRowRecordsModel with datahash."""
        if not datahash:
            raise ValueError("Data hash must be provided.")

        excel_row_record, created = (
            recon_models.ExcelRowRecordsModel.objects.get_or_create(
                datahash=datahash
            )
        )
        if created:
            logger.info(f"Created new ExcelRowRecordsModel for {datahash=}")
            return excel_row_record

        if not excel_row_record.is_processed_done:
            logger.debug(f"record({datahash[-5:]}) has not completed processing...")
            return excel_row_record

        if excel_row_record.is_processed_done:
            raise SkipException(
                f"record({datahash[-5:]}) already exists + processed. skipping..."
            )

    def parse_single_row(self, doc: dict):
        datahash = doc.get("data_hash")
        user_model = get_user_model()
        user_admin = user_model.objects.get(username=settings.DJANGO_SUPERUSER_ADMIN)

        if not datahash:
            raise SkipException("document without data_hash.")
        try:
            excel_row_record = self.register_update_record(datahash)
        except SkipException as se:
            raise se

        # Create or verify LeadingOrderModel
        lo_obj = self.create_leading_order(doc)
        # Link Customer Service Representative to LeadingOrderModel
        self.create_cs_rep_relationship(doc, lo_obj=lo_obj)

        # Create or verify Engine Part
        eg_part_obj = self.create_engine_part(doc)

        # print(f"{eg_part_obj=}")
        eg_part_record_obj = self.create_engine_part_record(
            doc=doc, engine_part=eg_part_obj
        )

        oh_scvl_obj = self.create_vendor_location(doc)

        # # Create carrier records
        carrier_in = self.create_carrier_record(doc, direction="in")
        carrier_out = self.create_carrier_record(doc, direction="out")

        # # Create OhRecordModel
        oh_record_obj = outhouse_models.OhRecordModel(
            ro_number=doc.get("ro_no"),
            leading_order=lo_obj,
            engine_part_record=eg_part_record_obj,
            subcon_vendor_location=oh_scvl_obj,
            carrier_record_in=carrier_in,
            carrier_record_out=carrier_out,
        )
        oh_record_obj = write_hash_to_transaction(oh_record_obj, doc)
        oh_record_obj.user_created_id = user_admin
        oh_record_obj.flow = outhouse_models.FlowModel.objects.get_or_create(
            name="flow_default"
        )[0]
        oh_record_obj.save()
        logger.info(f"Created OhRecordModel for {oh_record_obj.ro_number=}")
        excel_row_record.is_processed_done = True
        excel_row_record.save()
        return oh_record_obj

    def parse(self) -> pd.DataFrame:
        # TODO: trigger mass data load
        counter = 0
        limit = 10
        for doc in self.iter_all():
            counter += 1
            logger.info(f"[{counter}] Processing document...")
            try:
                _ = self.parse_single_row(doc)
            except SkipException as se:
                logger.info(f"{se}")
                limit += 1
                continue

            if counter > limit:
                break

    def create_carrier_record(
        self,
        doc: dict,
        direction: str,
        direction_mapping: dict = {"out": "awb_ship_to_vdr", "in": "awb_ship_to_st"},
    ):
        match direction.casefold():
            case "in":
                col = direction_mapping.get("in", None)
            case "out":
                col = direction_mapping.get("out", None)
            case _:
                raise ValueError("Invalid direction.")
        if not col:
            raise ValueError("invalid direction_mapping")
        awb_str = str(doc.get(col)).strip()
        if not awb_str:
            return
        try:
            parsed_data = parse_awb_data(awb_str)
        except ValueError as e:
            logger.debug(f"skipped parsing AWB data: {e}")
            return
        carrier_object, created = outhouse_models.CarrierModel.objects.get_or_create(
            name=parsed_data["vendor"].lower().strip().replace(" ", "")
        )
        if created:
            carrier_object.name = parsed_data["vendor"]
        else:
            if carrier_object.name != parsed_data["vendor"]:
                raise ValueError(
                    f"CarrierModel {carrier_object.pk} exists with different name ({carrier_object.name} != {parsed_data['vendor']}). Deconflict required."
                )
        carrier_record = outhouse_models.CarrierRecordModel(
            carrier=carrier_object,
            direction=direction.upper(),
            awb=parsed_data["awb"],
            awb_main=parsed_data["mawb"],
            awb_house=parsed_data["hawb"],
        )
        carrier_record.save()
        return carrier_record

    def create_vendor_location(
        self,
        doc: dict,
        vendor_code: str = "vendor_code",
        vendor_str: str = "vendor",
        dropship_str: str = "dropship_address",
    ) -> outhouse_models.SubconVendorLocationModel:
        """Create or update SubconVendorLocationModel from document."""
        vendor_name = doc.get(vendor_str)
        if not vendor_name:
            raise ValueError(f"Document must contain '{vendor_str}' field.")
        vendor_code = doc.get(vendor_code, None)
        if vendor_code is None:
            vendor_code = convert_to_snake_case(vendor_name)

        vendor_obj, is_created = (
            outhouse_models.SubconVendorModel.objects.get_or_create(code=vendor_code)
        )

        if is_created:
            vendor_obj.name = vendor_name
            vendor_obj.save()
            logger.info(f"Created new SubconVendorModel for {vendor_code=}")
        else:
            if vendor_obj.name.casefold() != vendor_name.casefold():
                raise ValueError(
                    f"SubconVendorModel {vendor_code} exists with different name ({vendor_obj.name} != {vendor_name}). Deconflict required."
                )

        dropship = convert_to_snake_case(doc.get(dropship_str, "default"))
        svl_obj, created = (
            outhouse_models.SubconVendorLocationModel.objects.get_or_create(
                vendor=vendor_obj,
                dropship=dropship,
            )
        )
        if created:
            logger.info(
                f"Created new SubconVendorLocationModel for {vendor_obj=} {dropship=}"
            )
        svl_obj.save()
        return svl_obj

    def create_engine_part_record(
        self,
        doc: dict,
        engine_part: engine_models.EnginePartModel,
        qty_str: str = "qty",
    ) -> engine_models.EnginePartRecordModel:
        """Create or update EnginePartRecordModel from document."""
        qty = doc.get(qty_str)
        if not qty:
            raise ValueError("Document must contain 'qty' field.")
        datahash = doc.get("data_hash", None)
        if not datahash:
            raise ValueError("Document must contain 'data_hash' field.")
        try:
            eg_part_record_obj = engine_models.EnginePartRecordModel.objects.get(
                data_from_hash=datahash
            )
            return eg_part_record_obj
        except engine_models.EnginePartRecordModel.DoesNotExist as dne:
            eg_part_record_obj = engine_models.EnginePartRecordModel(
                engine_part=engine_part,
                qty=qty,
                data_from_hash=datahash,
            )
            uom = doc.get("uom", None)
            if uom is not None:
                uom_obj, is_created = (
                    engine_models.UnitOfMeasurementModel.objects.get_or_create(abbr=uom)
                )
                if is_created:
                    logger.info(f"Created new UnitOfMeasurementModel for {uom_obj=}")
                eg_part_record_obj.uom = uom_obj
            eg_part_record_obj.save()
            logger.info(
                f"Created new EnginePartRecordModel for {engine_part=} with {datahash=}"
            )
        return eg_part_record_obj

    def create_engine_part(
        self,
        doc: dict,
        part_no_str: str = "part_no",
        description_str: str = "description",
    ) -> engine_models.EnginePartModel:
        """Create or update EnginePartModel from document."""
        part_number = doc.get(part_no_str, None)
        if not part_number:
            raise ValueError(f"Document must contain '{part_no_str}' field.")
        description = doc.get(description_str, None)
        if not description:
            raise ValueError(f"Document must contain '{description}' field.")

        eg_part_obj, is_created = engine_models.EnginePartModel.objects.get_or_create(
            part_number=part_number, description=description
        )
        if is_created:
            logger.info(f"Created new EnginePartModel for {part_number=}")
        eg_part_obj.save()  # this steps triggers the uid generation
        return eg_part_obj

    def create_leading_order(self, doc: dict) -> engine_models.LeadingOrderModel:
        """Create or update LeadingOrderModel from document."""
        lo_id = doc.get("job_no")
        esn = doc.get("esn")
        if not lo_id or not esn:
            raise ValueError("Document must contain 'job_no' and 'esn' fields.")

        lo_obj, created = engine_models.LeadingOrderModel.objects.get_or_create(
            lo_number=lo_id
        )
        if created:
            logger.info(f"Created new LeadingOrderModel for {esn=}")
            lo_obj.esn = esn
            lo_obj.save()
        else:
            if str(lo_obj.esn) != str(esn):
                raise ValueError(
                    f"LeadingOrderModel {lo_id} exists with different ESN ({lo_obj.esn} != {esn}). Deconflict required."
                )
        lo_obj.save()
        return lo_obj

    def create_cs_rep_relationship(
        self,
        doc,
        csrep_str: str = "customer_service_rep",
        delimiter: str = "/",
        lo_obj: Optional[engine_models.LeadingOrderModel] = None,
    ):
        if lo_obj is None:
            lo_obj = self.create_leading_order(doc)
        cs_names = doc.get(csrep_str)
        cs_names = cs_names.replace(" ", "").lower().strip()
        for name in cs_names.split(delimiter):
            self.link_cs_rep_to_leading_order(name, lo_obj)

    def link_cs_rep_to_leading_order(
        self, csrep_username: str, lo_obj: engine_models.LeadingOrderModel
    ) -> engine_models.LeadingOrderModel:
        cs_user, created = account_models.UserModel.objects.get_or_create(
            username=csrep_username
        )
        dept_role_obj, created = (
            account_models.DepartmentRoleModel.objects.get_or_create(
                name="csrep",
                description="Customer service representative",
            )
        )
        cs_user.department_role = dept_role_obj
        cs_user.save()
        lo_obj.oh_csrep.add(cs_user)
        lo_obj.save()
        return lo_obj

    def run(self) -> int:
        """Orchestrates ETL pipeline, loading into MongoDB."""
        logger.info("ETL pipeline started for Outhouse SubCon data seeding...")
        self.db.connect()
        self.db.init_collection(self.collection_name, index_names=["data_hash"])
        self.db.check_read_write_access()
        self.parse()


def main():
    """Main entry point for the PPCS Outhouse seeder."""

    mgdb = MongoDbHelper(connection_str=settings.MGDB_CONNECTION_STR)

    # Load the SubCon data
    try:
        trf = OhSubconExcelDataTransformer(
            mongo_db=mgdb,
            collection_name=config["etl_subcon_excel"][
                "collection_name_extract_userinput"
            ],
        )
        trf.run()
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e=}")
        raise SystemExit(1)


if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()
    main()
