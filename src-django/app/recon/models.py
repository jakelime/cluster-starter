# recon/models.py
import logging
from pathlib import Path

from celery.result import AsyncResult
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse

from recon.enums import ChoicesReportStatus

lg = logging.getLogger("django")
MATR_CONF = settings.MATR_CONF
SALES_CONF = settings.SALES_CONF
OPS_CONF = settings.OPS_CONF
HELLO_CONF = settings.HELLO_CONF

UserModel = get_user_model()


def shorten_pathname(path: Path, max_length: int = 10) -> str:
    name = path.name
    suffix = path.suffix
    if len(name) >= max_length:
        name = f"{name[:max_length]}...{suffix}"
    return name


class TaskAbstractModel(models.Model):
    task_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(
        max_length=32,
        default=ChoicesReportStatus.NONE,
        blank=True,
        choices=ChoicesReportStatus.choices,
    )
    result = models.TextField(null=True, blank=True)

    traceback = models.TextField(null=True, blank=True)
    fetched_completed = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    dt_created = models.DateTimeField(auto_now_add=True)
    dt_start = models.DateTimeField(null=True, blank=True)
    dt_end = models.DateTimeField(null=True, blank=True)
    processing_time = models.FloatField(default=0.0, blank=True)

    user_created = models.ForeignKey(
        UserModel,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(app_label)s_%(class)s_user_created",
    )

    def __str__(self):
        return f"Task {self.task_id} - Status: {self.status}"

    def get_absolute_url(self):
        return reverse("recon:task_detail", kwargs={"pk": self.pk})

    def get_celery_task_url(self):
        return reverse("recon:celery_task_detail") + f"?taskid={self.task_id}"

    def fetch_update(self) -> None:
        if self.fetched_completed:
            return
        try:
            task = AsyncResult(self.task_id)
            self.status = str(task.status)
            self.result = str(task.result)
            self.completed = task.ready()
            if self.completed:
                self.fetched_completed = True
            self.dt_end = task.date_done
            self.traceback = str(task.traceback)
            self.save()
        except Exception as e:
            raise Exception(f"unable to fetch update from {self.task_id=}") from e

    def calculate_processing_time(self) -> float:
        ptime = 0.0
        if self.dt_start and self.dt_end:
            ptime = (self.dt_end - self.dt_start).total_seconds()
        return ptime

    class Meta:
        abstract = True


class FileUploadModel(TaskAbstractModel):
    input_fpath = models.FileField(
        blank=False,
        null=True,
        max_length=2048,
        upload_to=settings.MEDIA_ROOT,
    )
    output_fpath = models.FileField(
        blank=True,
        null=True,
        max_length=2048,
        upload_to=settings.MEDIA_ROOT,
    )

    class Meta:
        abstract = True

    def get_output_url(self) -> str:
        try:
            return self.output_fpath.url
        except Exception:
            return "#"

    def get_output_name(self) -> str:
        if not self.output_fpath:
            return ""
        return shorten_pathname(Path(self.output_fpath.path))

    def get_input_url(self) -> str:
        try:
            return self.input_fpath.url
        except Exception:
            return "#"

    def get_input_name(self) -> str:
        if not self.input_fpath:
            return ""
        return shorten_pathname(Path(self.input_fpath.path))


class Zmmr3010ReportModel(FileUploadModel):
    name = models.CharField(max_length=256, unique=False, null=True, blank=True)

    input_fpath = models.FileField(
        blank=False,
        null=True,
        max_length=2048,
        upload_to=MATR_CONF.INPUT_DIRNAME_ZMMR3010,
        validators=[FileExtensionValidator(allowed_extensions=["", ".txt"])],
    )
    output_fpath = models.FileField(
        blank=True,
        null=True,
        max_length=2048,
        upload_to=MATR_CONF.OUTPUT_DIRNAME_ZMMR3010,
    )

    def __str__(self):
        try:
            return f"{self.__class__.__name__}({self.name}, {self.dt_created.strftime('%Y%m%d_%H%MH')})"
        except AttributeError:
            return f"{self.__class__.__name__}(AttributeError: pk={self.pk})"

    def get_delete_url(self):
        return reverse("recon:zmmr3010_delete", kwargs={"pk": self.pk})

    def get_update_url(self):
        return reverse("recon:zmmr3010_update", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        if not self.name:
            try:
                path = Path(self.input_fpath.path)
                self.name = path.name
            except Exception as e:
                lg.warning(f"error saving MatrReportModel; {e=}")
        self.name = self.name.strip().replace(" ", "").lower()
        super().save(*args, **kwargs)


class LeadingOrderFileUploadModel(FileUploadModel):
    name = models.CharField(max_length=256, unique=False, null=True, blank=True)
    input_fpath = models.FileField(
        blank=False,
        null=True,
        max_length=2048,
        upload_to=MATR_CONF.INPUT_DIRNAME_LEADINGORDER,
        validators=[FileExtensionValidator(allowed_extensions=["json", "gz"])],
    )
    rows_inserted = models.IntegerField(blank=True, null=True)

    def __str__(self):
        try:
            return f"{self.__class__.__name__}({self.name}, {self.dt_created.strftime('%Y%m%d_%H%MH')})"
        except AttributeError:
            return f"{self.__class__.__name__}(AttributeError: pk={self.pk})"

    def get_delete_url(self):
        return reverse("recon:lo_fileupload_delete", kwargs={"pk": self.pk})

    def get_update_url(self):
        return reverse("recon:lo_fileupload_update", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        if not self.name:
            try:
                path = Path(self.input_fpath.path)
                self.name = path.name
            except Exception as e:
                lg.warning(f"error saving LeadingOrderFileUploadModel; {e=}")
        self.name = self.name.strip().replace(" ", "").lower()
        super().save(*args, **kwargs)


class LeadingOrderTransformModel(TaskAbstractModel):
    rows_transformed = models.IntegerField(default=0)


class SalesFileUploadModel(FileUploadModel):
    name = models.CharField(max_length=256, unique=False, null=True, blank=True)
    input_fpath = models.FileField(
        blank=False,
        null=True,
        max_length=2048,
        upload_to=SALES_CONF.INPUT_DIRNAME_SALES,
        validators=[FileExtensionValidator(allowed_extensions=["xlsx", "xlsm"])],
    )
    rows_inserted = models.IntegerField(blank=True, null=True)

    def __str__(self):
        try:
            return f"{self.__class__.__name__}({self.name}, {self.dt_created.strftime('%Y%m%d_%H%MH')})"
        except AttributeError:
            return f"{self.__class__.__name__}(AttributeError: pk={self.pk})"

    def get_delete_url(self):
        return reverse("recon:sales_fileupload_delete", kwargs={"pk": self.pk})

    def get_update_url(self):
        return reverse("recon:sales_fileupload_update", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        if not self.name:
            try:
                path = Path(self.input_fpath.path)
                self.name = path.name
            except Exception as e:
                lg.warning(f"error saving SalesFileUploadModel; {e=}")
        self.name = self.name.strip().replace(" ", "").lower()
        super().save(*args, **kwargs)


class SalesTransformModel(TaskAbstractModel):
    rows_transformed = models.IntegerField(default=0)


class OpsFileUploadModel(FileUploadModel):
    name = models.CharField(max_length=256, unique=False, null=True, blank=True)
    input_fpath = models.FileField(
        blank=False,
        null=True,
        max_length=2048,
        upload_to=OPS_CONF.INPUT_DIRNAME_OPS,
        validators=[FileExtensionValidator(allowed_extensions=["xlsx", "xlsm"])],
    )
    rows_inserted = models.IntegerField(blank=True, null=True)

    def __str__(self):
        try:
            return f"{self.__class__.__name__}({self.name}, {self.dt_created.strftime('%Y%m%d_%H%MH')})"
        except AttributeError:
            return f"{self.__class__.__name__}(AttributeError: pk={self.pk})"

    def get_delete_url(self):
        return reverse("recon:ops_fileupload_delete", kwargs={"pk": self.pk})

    def get_update_url(self):
        return reverse("recon:ops_fileupload_update", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        if not self.name:
            try:
                path = Path(self.input_fpath.path)
                self.name = path.name
            except Exception as e:
                lg.warning(f"error saving OpsFileUploadModel; {e=}")
        self.name = self.name.strip().replace(" ", "").lower()
        super().save(*args, **kwargs)


class OpsTransformModel(TaskAbstractModel):
    rows_transformed = models.IntegerField(default=0)


class HelloModel(FileUploadModel):
    name = models.CharField(max_length=256, unique=False, null=True, blank=True)

    input_fpath = models.FileField(
        blank=False,
        null=True,
        max_length=2048,
        upload_to=MATR_CONF.INPUT_DIRNAME_ZMMR3010,
        validators=[
            FileExtensionValidator(allowed_extensions=HELLO_CONF.INPUT_ALLOWED_EXTENSIONS)
        ],
    )

    def __str__(self):
        try:
            return f"{self.__class__.__name__}({self.name}, {self.dt_created.strftime('%Y%m%d_%H%MH')})"
        except AttributeError:
            return f"{self.__class__.__name__}(AttributeError: pk={self.pk})"

    def get_delete_url(self):
        raise NotImplementedError()

    def get_update_url(self):
        raise NotImplementedError()

    def save(self, *args, **kwargs):
        if not self.name:
            try:
                path = Path(self.input_fpath.path)
                self.name = path.name
                self.name = self.name.strip().replace(" ", "").lower()
            except Exception as e:
                lg.warning(f"error saving HelloWorldModel; {e=}")

        super().save(*args, **kwargs)
