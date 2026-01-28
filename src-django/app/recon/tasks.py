# jetforge/recon/tasks.py
import logging
from pathlib import Path

from app import models as config_models
from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.shortcuts import get_object_or_404
from django.utils import timezone
from main.config import ConfigHelper
from main.utils import retry_on_exception

from recon.enums import ChoicesReportStatus as CRS
from recon.etl.django.leadingorders import extract as lo_extractor
from recon.etl.django.leadingorders import transform as lo_transform
from recon.etl.django.ops import transform as ops_transform
from recon.etl.django.ops.extract import CONFIG as OPS_PARSER_CONFIG
from recon.etl.django.ops.extract import OpsExtractor
from recon.etl.django.salesfinance import transform as sales_transform
from recon.etl.django.salesfinance.extract import SalesExtractor
from recon.etl.django.zmmr3010.extract import MaterialsProcessor
from recon.models import (
    LeadingOrderFileUploadModel,
    LeadingOrderTransformModel,
    OpsFileUploadModel,
    OpsTransformModel,
    SalesFileUploadModel,
    SalesTransformModel,
    Zmmr3010ReportModel,
    HelloModel,
)

cf = ConfigHelper()
config = cf.config
lg = logging.getLogger("django")


@shared_task(bind=True)
def extract_hello(self, pk: str) -> str:
    record = None
    try:
        record = get_object_or_404(HelloModel, pk=pk)
        # Check if the file exists before proceeding
        record.task_id = self.request.id
        record.dt_start = timezone.now()
        record.status = CRS.RUNNING
        record.save(update_fields=["status", "task_id", "dt_start"])

        fpath = check_file_exists(Path(record.input_fpath.path))
        content = fpath.read_text(encoding="utf-8")
        record.data = content
        record.save(update_fields=["data"])

        record.status = CRS.DONE
        record.dt_end = timezone.now()
        record.processing_time = record.calculate_processing_time()
        record.save(
            update_fields=["status", "dt_end", "processing_time", "output_fpath"]
        )
        results = f"hello world!({pk=}) done."
    except Exception as e:
        if record:
            record.status = CRS.FAILED
            record.save(update_fields=["status"])
        results = f"extract_hello({pk=}) failed:, error={e}"
        lg.error(results)

    return results


@retry_on_exception(
    max_attempts=5,
    base_delay=10,
    max_delay=30,
    exceptions_to_catch=(FileNotFoundError,),
)
def check_file_exists(filepath_str: str) -> Path:
    # Sometimes, task is started before the file is written to disk.
    # This function will retry checking the file existence.
    filepath = Path(filepath_str)
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath=}")
    return filepath


@shared_task(bind=True)
def extractload_zmmr3010(self, pk: str) -> str:
    record = None
    matp = MaterialsProcessor()
    try:
        record = get_object_or_404(Zmmr3010ReportModel, pk=pk)
        # Check if the file exists before proceeding
        fpath = check_file_exists(Path(record.input_fpath.path))
        record.task_id = self.request.id
        record.dt_start = timezone.now()
        record.status = CRS.RUNNING
        record.save(update_fields=["status", "task_id", "dt_start"])
        outpath = matp.run(input_fpath=fpath, outname=fpath.name)
        if outpath is None or not outpath.exists():
            record.status = CRS.FAILED
            record.dt_end = timezone.now()
            record.processing_time = record.calculate_processing_time()
            record.save(update_fields=["status", "processing_time"])
            return f"extractload_zmmr3010({pk=}) failed. error=Output file was not created."

        # Saves output path to Django model using Django File
        django_file = File(str(outpath.absolute()))
        with open(outpath, "rb") as f:
            django_file = File(f)
            record.output_fpath.save(outpath.name, django_file, save=True)
        record.status = CRS.DONE
        record.dt_end = timezone.now()
        record.processing_time = record.calculate_processing_time()
        record.save(
            update_fields=["status", "dt_end", "processing_time", "output_fpath"]
        )
        results = f"extractload_zmmr3010({pk=}) done."
    except Exception as e:
        if record:
            record.status = CRS.FAILED
            record.save(update_fields=["status"])
        results = f"extractload_zmmr3010({pk=}) failed:, error={e}"
        lg.error(results)

    return results


@shared_task(bind=True)
def extractload_leadingorder(self, pk: str) -> str:
    datarows_inserted = 0
    record = None
    lg.info("extractload_leadingorder  is running...")
    try:
        record = get_object_or_404(LeadingOrderFileUploadModel, pk=pk)
        lg.info(f"Processing LeadingOrderFileUploadModel with pk={pk}")
        check_file_exists(Path(record.input_fpath.path))
        record.task_id = self.request.id
        record.dt_start = timezone.now()
        record.status = CRS.RUNNING
        record.save(update_fields=["status", "task_id", "dt_start"])
        datarows_inserted = None
    except LeadingOrderFileUploadModel.DoesNotExist:
        lg.error(f"LeadingOrderFileUploadModel with pk={pk} does not exist.")
        return f"extractload_leadingorder ({pk=}) failed. error=Record not found."

    try:
        loe = lo_extractor.LeadingOrderExtractor(
            conn_str=settings.MGDB_CONNECTION_STR,
            input_fpath=Path(record.input_fpath.path),
        )
        datarows_inserted = loe.run()
    except Exception as e:
        lg.error(f"Error during LeadingOrderExtractor run: {e}")
        record.status = CRS.FAILED
        record.dt_end = timezone.now()
        record.processing_time = record.calculate_processing_time()
        record.save(update_fields=["status", "dt_end", "processing_time"])
        return f"extractload_leadingorder ({pk=}) failed. error={e}"

    if datarows_inserted:
        record.status = CRS.DONE
        record.dt_end = timezone.now()
        record.processing_time = record.calculate_processing_time()
        record.save(update_fields=["status", "dt_end", "processing_time"])
        return f"extractload_leadingorder ({pk=}) {datarows_inserted=}."

    else:
        if datarows_inserted == 0:
            record.status = CRS.DONE
            record.dt_end = timezone.now()
            record.processing_time = record.calculate_processing_time()
            record.save(update_fields=["status", "dt_end", "processing_time"])
            return f"extractload_leadingorder ({pk=}) {datarows_inserted=}."
        else:
            record.status = CRS.UNKNOWN_ERROR
            record.dt_end = timezone.now()
            record.processing_time = record.calculate_processing_time()
            record.save(update_fields=["status", "dt_end", "processing_time"])
            return f"UNKNOWN ERROR. extractload_leadingorder ({pk=}); {datarows_inserted=}."


@shared_task(bind=True)
def transform_leadingorder(self, pk: str) -> str:
    # 1. Prep
    rows_transformed = 0
    record = None
    lg.info("transform_leadingorder  is running...")
    try:
        record = get_object_or_404(LeadingOrderTransformModel, pk=pk)

        lg.info(f"Processing LeadingOrderTransformModel with pk={pk}")
        record.task_id = self.request.id
        record.dt_start = timezone.now()
        record.status = CRS.RUNNING
        record.save(update_fields=["status", "task_id", "dt_start"])
    except LeadingOrderTransformModel.DoesNotExist:
        lg.error(f"LeadingOrderTransformModel with pk={pk} does not exist.")
        return f"transform_leadingorder ({pk=}) failed. error=Record not found."

    # 2. Run action
    try:
        rows_transformed = lo_transform.transform()
    except Exception as e:
        lg.error(f"Error during LeadingOrderExtractor run: {e}")
        record.status = CRS.FAILED
        record.dt_end = timezone.now()
        record.processing_time = record.calculate_processing_time()
        record.save(update_fields=["status", "dt_end", "processing_time"])
        return f"transform_leadingorder ({pk=}) failed. error={e}"

    # 3. Save results
    if rows_transformed:
        record.status = CRS.DONE
        record.rows_transformed = rows_transformed
        record.dt_end = timezone.now()
        record.processing_time = record.calculate_processing_time()
        record.save(
            update_fields=["status", "dt_end", "processing_time", "rows_transformed"]
        )
        return f"transform_leadingorder ({pk=}) {rows_transformed=}."

    else:
        if rows_transformed == 0:
            record.status = CRS.DONE
            record.rows_transformed = rows_transformed
            record.dt_end = timezone.now()
            record.processing_time = record.calculate_processing_time()
            record.save(
                update_fields=[
                    "status",
                    "dt_end",
                    "processing_time",
                    "rows_transformed",
                ]
            )
            return f"transform_leadingorder ({pk=}) {rows_transformed=}."
        else:
            record.status = CRS.UNKNOWN_ERROR
            record.dt_end = timezone.now()
            record.processing_time = record.calculate_processing_time()
            record.save(update_fields=["status", "dt_end", "processing_time"])
            return (
                f"UNKNOWN ERROR. transform_leadingorder ({pk=}); {rows_transformed=}."
            )


@shared_task(bind=True)
def extractload_sales(self, pk: str) -> str:
    user_model = get_user_model()
    user_admin = user_model.objects.get(username=settings.DJANGO_SUPERUSER_ADMIN)
    datarows_inserted = 0
    record = None
    lg.info("extractload_sales is running...")

    try:
        user_config_cfm, is_created_cfm = (
            config_models.ConfigSettingsModel.objects.get_or_create(
                name="parser-excel-sales-cfm"
            )
        )
        if is_created_cfm:
            lg.info("initializing user_config_cfm...")
            user_config_cfm.config = settings.SALES_CONF.DEFAULTS_EXCEL_PARSER_CFM
            user_config_cfm.user_created = user_admin
            user_config_cfm.save()

        user_config_leap, is_created_leap = (
            config_models.ConfigSettingsModel.objects.get_or_create(
                name="parser-excel-sales-leap"
            )
        )
        if not user_config_cfm.config:
            raise ValueError(f"config is empty or None; {user_config_cfm.config=}")

        if is_created_leap:
            lg.info("initializing user_config_cfm...")
            user_config_leap.config = settings.SALES_CONF.DEFAULTS_EXCEL_PARSER_LEAP
            user_config_leap.user_created = user_admin
            user_config_leap.save()

        if not user_config_leap.config:
            raise ValueError(f"config is empty or None; {user_config_leap.config=}")

    except Exception as e:
        lg.error(f"Error loading dynamic user-config; {e=}")
        raise RuntimeError(
            f"extractload_sales({pk=}) failed: error loading user-config."
        ) from e

    try:
        record = get_object_or_404(SalesFileUploadModel, pk=pk)
        lg.info(f"Processing SalesFileUploadModel with pk={pk}")
        check_file_exists(Path(record.input_fpath.path))
        record.task_id = self.request.id
        record.dt_start = timezone.now()
        record.status = CRS.RUNNING
        record.save(update_fields=["status", "task_id", "dt_start"])
        datarows_inserted = None
    except SalesFileUploadModel.DoesNotExist:
        lg.error(f"SalesFileUploadModel with pk={pk} does not exist.")
        raise RuntimeError(
            f"extractload_sales({pk=}) failed: SalesFileUploadModel object not found."
        )

    datarows_inserted = 0

    try:
        cfm_sales = SalesExtractor(
            conn_str=settings.MGDB_CONNECTION_STR,
            input_fpath=Path(record.input_fpath.path),
            config=user_config_cfm.config,
        )
        datarows_inserted += cfm_sales.run()
    except Exception as e:
        lg.error(f"Error during SalesExtractor run: {e}")
        record.status = CRS.FAILED
        record.dt_end = timezone.now()
        record.processing_time = record.calculate_processing_time()
        record.save(update_fields=["status", "dt_end", "processing_time"])
        raise RuntimeError(
            f"task:extractload_sales({pk=}): SalesExtractor(cfm_sales) fn failed"
        ) from e

    try:
        leap_sales = SalesExtractor(
            conn_str=settings.MGDB_CONNECTION_STR,
            input_fpath=Path(record.input_fpath.path),
            config=user_config_leap.config,
        )
        datarows_inserted += leap_sales.run()

    except Exception as e:
        lg.error(f"Error during SalesExtractor run: {e}")
        record.status = CRS.FAILED
        record.dt_end = timezone.now()
        record.processing_time = record.calculate_processing_time()
        record.save(update_fields=["status", "dt_end", "processing_time"])
        raise RuntimeError(
            f"task:extractload_sales({pk=}): SalesExtractor(leap_sales) fn failed"
        ) from e

    if datarows_inserted:
        record.status = CRS.DONE
        record.dt_end = timezone.now()
        record.processing_time = record.calculate_processing_time()
        record.save(update_fields=["status", "dt_end", "processing_time"])
        return f"extractload_sales ({pk=}) {datarows_inserted=}."

    else:
        if datarows_inserted == 0:
            record.status = CRS.DONE
            record.dt_end = timezone.now()
            record.processing_time = record.calculate_processing_time()
            record.save(update_fields=["status", "dt_end", "processing_time"])
            return f"extractload_sales ({pk=}) {datarows_inserted=}."
        else:
            record.status = CRS.UNKNOWN_ERROR
            record.dt_end = timezone.now()
            record.processing_time = record.calculate_processing_time()
            record.save(update_fields=["status", "dt_end", "processing_time"])
            return f"UNKNOWN ERROR. extractload_sales ({pk=}); {datarows_inserted=}."


@shared_task(bind=True)
def transform_sales(self, pk: str) -> str:
    # 1. Prep
    rows_transformed = 0
    record = None
    lg.info("transform_sales  is running...")
    try:
        record = get_object_or_404(SalesTransformModel, pk=pk)

        lg.info(f"Processing SalesTransformModel with pk={pk}")
        record.task_id = self.request.id
        record.dt_start = timezone.now()
        record.status = CRS.RUNNING
        record.save(update_fields=["status", "task_id", "dt_start"])
    except SalesTransformModel.DoesNotExist:
        lg.error(f"SalesTransformModel with pk={pk} does not exist.")
        return f"transform_sales ({pk=}) failed. error=Record not found."

    # 2. Run action
    try:
        rows_transformed = sales_transform.transform()
    except Exception as e:
        lg.error(f"Error during SalesTransform run: {e}")
        record.status = CRS.FAILED
        record.dt_end = timezone.now()
        record.processing_time = record.calculate_processing_time()
        record.save(update_fields=["status", "dt_end", "processing_time"])
        return f"transform_sales ({pk=}) failed. error={e}"

    # 3. Save results
    if rows_transformed:
        record.status = CRS.DONE
        record.rows_transformed = rows_transformed
        record.dt_end = timezone.now()
        record.processing_time = record.calculate_processing_time()
        record.save(
            update_fields=["status", "dt_end", "processing_time", "rows_transformed"]
        )
        return f"transform_sales ({pk=}) {rows_transformed=}."

    else:
        if rows_transformed == 0:
            record.status = CRS.DONE
            record.rows_transformed = rows_transformed
            record.dt_end = timezone.now()
            record.processing_time = record.calculate_processing_time()
            record.save(
                update_fields=[
                    "status",
                    "dt_end",
                    "processing_time",
                    "rows_transformed",
                ]
            )
            return f"transform_sales ({pk=}) {rows_transformed=}."
        else:
            record.status = CRS.UNKNOWN_ERROR
            record.dt_end = timezone.now()
            record.processing_time = record.calculate_processing_time()
            record.save(update_fields=["status", "dt_end", "processing_time"])
            return f"UNKNOWN ERROR. transform_sales ({pk=}); {rows_transformed=}."


@shared_task(bind=True)
def extractload_ops(self, pk: str) -> str:
    datarows_inserted = 0
    record = None
    lg.info("extractload_ops  is running...")
    try:
        record = get_object_or_404(OpsFileUploadModel, pk=pk)
        lg.info(f"Processing OpsFileUploadModel with pk={pk}")
        check_file_exists(Path(record.input_fpath.path))
        record.task_id = self.request.id
        record.dt_start = timezone.now()
        record.status = CRS.RUNNING
        record.save(update_fields=["status", "task_id", "dt_start"])
        datarows_inserted = None
    except OpsFileUploadModel.DoesNotExist:
        lg.error(f"OpsFileUploadModel with pk={pk} does not exist.")
        return f"extractload_ops ({pk=}) failed. error=Record not found."

    try:
        # TODO: Test and validate if this is functional in Django
        lg.info("etl entrypoint.py is running...")
        datarows_inserted = 0
        cfm_ops = OpsExtractor(
            conn_str=settings.MGDB_CONNECTION_STR,
            input_fpath=Path(record.input_fpath.path),
            config=OPS_PARSER_CONFIG.get("cfm56-excel-parser"),
        )
        datarows_inserted += cfm_ops.run()

        leap_engine_ops = OpsExtractor(
            conn_str=settings.MGDB_CONNECTION_STR,
            input_fpath=Path(record.input_fpath.path),
            config=OPS_PARSER_CONFIG.get("leap-engine-excel-parser"),
        )
        datarows_inserted += leap_engine_ops.run()

        leap_module_ops = OpsExtractor(
            conn_str=settings.MGDB_CONNECTION_STR,
            input_fpath=Path(record.input_fpath.path),
            config=OPS_PARSER_CONFIG.get("leap-module-excel-parser"),
        )
        datarows_inserted += leap_module_ops.run()

    except Exception as e:
        lg.error("Error during OpsExtractor run: ", exc_info=True)
        record.status = CRS.FAILED
        record.dt_end = timezone.now()
        record.processing_time = record.calculate_processing_time()
        record.save(update_fields=["status", "dt_end", "processing_time"])
        return f"extractload_ops ({pk=}) failed. error={e}"

    if datarows_inserted:
        record.status = CRS.DONE
        record.dt_end = timezone.now()
        record.processing_time = record.calculate_processing_time()
        record.save(update_fields=["status", "dt_end", "processing_time"])
        return f"extractload_ops ({pk=}) {datarows_inserted=}."

    else:
        if datarows_inserted == 0:
            record.status = CRS.DONE
            record.dt_end = timezone.now()
            record.processing_time = record.calculate_processing_time()
            record.save(update_fields=["status", "dt_end", "processing_time"])
            return f"extractload_ops ({pk=}) {datarows_inserted=}."
        else:
            record.status = CRS.UNKNOWN_ERROR
            record.dt_end = timezone.now()
            record.processing_time = record.calculate_processing_time()
            record.save(update_fields=["status", "dt_end", "processing_time"])
            return f"UNKNOWN ERROR. extractload_ops ({pk=}); {datarows_inserted=}."


@shared_task(bind=True)
def transform_ops(self, pk: str) -> str:
    # 1. Prep
    rows_transformed = 0
    record = None
    lg.info("transform_ops  is running...")
    try:
        record = get_object_or_404(OpsTransformModel, pk=pk)

        lg.info(f"Processing OpsTransformModel with pk={pk}")
        record.task_id = self.request.id
        record.dt_start = timezone.now()
        record.status = CRS.RUNNING
        record.save(update_fields=["status", "task_id", "dt_start"])
    except OpsTransformModel.DoesNotExist:
        lg.error(f"OpsTransformModel with pk={pk} does not exist.")
        return f"transform_ops ({pk=}) failed. error=Record not found."

    # 2. Run action
    try:
        rows_transformed = ops_transform.transform()
    except Exception as e:
        lg.error(f"Error during OpsTransform run: {e}")
        record.status = CRS.FAILED
        record.dt_end = timezone.now()
        record.processing_time = record.calculate_processing_time()
        record.save(update_fields=["status", "dt_end", "processing_time"])
        return f"transform_ops ({pk=}) failed. error={e}"

    # 3. Save results
    if rows_transformed:
        record.status = CRS.DONE
        record.rows_transformed = rows_transformed
        record.dt_end = timezone.now()
        record.processing_time = record.calculate_processing_time()
        record.save(
            update_fields=["status", "dt_end", "processing_time", "rows_transformed"]
        )
        return f"transform_sales ({pk=}) {rows_transformed=}."

    else:
        if rows_transformed == 0:
            record.status = CRS.DONE
            record.rows_transformed = rows_transformed
            record.dt_end = timezone.now()
            record.processing_time = record.calculate_processing_time()
            record.save(
                update_fields=[
                    "status",
                    "dt_end",
                    "processing_time",
                    "rows_transformed",
                ]
            )
            return f"transform_sales ({pk=}) {rows_transformed=}."
        else:
            record.status = CRS.UNKNOWN_ERROR
            record.dt_end = timezone.now()
            record.processing_time = record.calculate_processing_time()
            record.save(update_fields=["status", "dt_end", "processing_time"])
            return f"UNKNOWN ERROR. transform_sales ({pk=}); {rows_transformed=}."
    pass
