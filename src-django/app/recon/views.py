# jetforge/recon/views.py
import logging
import threading
from typing import Any

from celery.result import AsyncResult
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.forms.models import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin, SingleTableView

from recon import appfilters, apptables, models, tasks
from recon import forms as appforms
from recon.enums import ChoicesReportStatus as CRS

lg = logging.getLogger("django")
MATR_CONF = settings.MATR_CONF


def load_zmmr3010_task_view(request, pk: str):
    record_for_display = get_object_or_404(models.Zmmr3010ReportModel, pk=pk)
    runnable_statuses = [
        CRS.NEW,
        CRS.FAILED,  # Allow retrying a failed task
    ]
    updated_count = models.Zmmr3010ReportModel.objects.filter(
        pk=pk, status__in=runnable_statuses
    ).update(status=CRS.QUEUED)  # Set status to QUEUED
    if updated_count == 0:
        messages.warning(
            request,
            f"Task for '{record_for_display.input_fpath.name}' is already in progress.",
        )
        return redirect(reverse("recon:zmmr3010_list"))

    # If we're here, updated_count was 1. We successfully claimed the task!
    # Now we can safely queue the Celery task.
    pk_str = str(pk)  # Keep doing this, it's correct for serialization
    lg.info(f"Queueing task for ZMMR3010 report with {pk_str=}")
    # We set a countdown to allow time for file upload to complete writing to disk.
    tasks.extractload_zmmr3010.apply_async((pk_str,), countdown=0)
    messages.success(
        request,
        f"Task for '{record_for_display.input_fpath.name}' has been successfully queued.",
    )
    return redirect(reverse("recon:zmmr3010_list"))


def load_lo_fileupload_task_view(request, pk: str):
    record_for_display = get_object_or_404(models.LeadingOrderFileUploadModel, pk=pk)
    runnable_statuses = [
        CRS.NEW,
        CRS.FAILED,  # Allow retrying a failed task
    ]
    updated_count = models.LeadingOrderFileUploadModel.objects.filter(
        pk=pk, status__in=runnable_statuses
    ).update(status=CRS.QUEUED)  # Set status to QUEUED
    if updated_count == 0:
        messages.warning(
            request,
            f"Task for '{record_for_display.input_fpath.name}' is already in progress.",
        )
        return redirect(reverse("recon:lo_fileupload_list"))

    # If we're here, updated_count was 1. We successfully claimed the task!
    # Now we can safely queue the Celery task.
    pk_str = str(pk)  # Keep doing this, it's correct for serialization
    lg.info(f"Queueing task for LeadingOrderFileUpload with {pk_str=}")
    # We set a countdown to allow time for file upload to complete writing to disk.
    tasks.extractload_leadingorder.apply_async((pk_str,), countdown=0)
    messages.success(
        request,
        f"Task for '{record_for_display.input_fpath.name}' has been successfully queued.",
    )
    return redirect(reverse("recon:lo_fileupload_list"))


def load_sales_fileupload_task_view(request, pk: str):
    record_for_display = get_object_or_404(models.SalesFileUploadModel, pk=pk)
    runnable_statuses = [
        CRS.NEW,
        CRS.FAILED,  # Allow retrying a failed task
    ]
    updated_count = models.SalesFileUploadModel.objects.filter(
        pk=pk, status__in=runnable_statuses
    ).update(status=CRS.QUEUED)  # Set status to QUEUED
    if updated_count == 0:
        messages.warning(
            request,
            f"Task for '{record_for_display.input_fpath.name}' is already in progress.",
        )
        return redirect(reverse("recon:sales_fileupload_list"))

    # If we're here, updated_count was 1. We successfully claimed the task!
    # Now we can safely queue the Celery task.
    pk_str = str(pk)  # Keep doing this, it's correct for serialization
    lg.info(f"Queueing task for SalesFileUpload with {pk_str=}")
    # We set a countdown to allow time for file upload to complete writing to disk.
    tasks.extractload_sales.apply_async((pk_str,), countdown=0)
    messages.success(
        request,
        f"Task for '{record_for_display.input_fpath.name}' has been successfully queued.",
    )
    return redirect(reverse("recon:sales_fileupload_list"))


def load_ops_fileupload_task_view(request, pk: str):
    record_for_display = get_object_or_404(models.OpsFileUploadModel, pk=pk)
    runnable_statuses = [
        CRS.NEW,
        CRS.FAILED,  # Allow retrying a failed task
    ]
    updated_count = models.OpsFileUploadModel.objects.filter(
        pk=pk, status__in=runnable_statuses
    ).update(status=CRS.QUEUED)  # Set status to QUEUED
    if updated_count == 0:
        messages.warning(
            request,
            f"Task for '{record_for_display.input_fpath.name}' is already in progress.",
        )
        return redirect(reverse("recon:ops_fileupload_list"))

    # If we're here, updated_count was 1. We successfully claimed the task!
    # Now we can safely queue the Celery task.
    pk_str = str(pk)  # Keep doing this, it's correct for serialization
    lg.info(f"Queueing task for OpsFileUpload with {pk_str=}")
    # We set a countdown to allow time for file upload to complete writing to disk.
    tasks.extractload_ops.apply_async((pk_str,), countdown=0)
    messages.success(
        request,
        f"Task for '{record_for_display.input_fpath.name}' has been successfully queued.",
    )
    return redirect(reverse("recon:ops_fileupload_list"))


class HomeView(TemplateView):
    template_name = "recon/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Connectors"
        return context


class CeleryTaskDetailView(LoginRequiredMixin, TemplateView):
    template_name = "recon/task-celery-detail.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        task_id = self.request.GET.get("taskid")

        if task_id:
            # Fetch the task result from the backend (Redis)
            task_result = AsyncResult(task_id)

            # Prepare data for the template
            context["celerytask"] = {
                "id": task_result.id,
                "status": task_result.status,
                "result": task_result.result,
                "traceback": task_result.traceback,
                "date_done": getattr(task_result, "date_done", None),
                # state is an alias for status, but sometimes holds specific meta
                "state": task_result.state,
            }
        else:
            context["celerytask"] = None
            context["error"] = "No taskid provided in the URL."

        context["page_title"] = "Celery Task Inspection"

        return context


class MaterialsConnectorsView(TemplateView):
    template_name = "recon/connectors-materials.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Materials Connectors"
        return context


class EnginesConnectorsView(TemplateView):
    template_name = "recon/connectors-engines.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Engines Connectors"
        return context


class SalesConnectorsView(TemplateView):
    template_name = "recon/connectors-sales.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Sales Connectors"
        return context


class OpsConnectorsView(TemplateView):
    template_name = "recon/connectors-ops.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Ops Connectors"
        return context


class Zmmr3010ReportListView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    SingleTableMixin,
    FilterView,
):
    model = models.Zmmr3010ReportModel
    table_class = apptables.Zmmr3010ReportActionTable
    filterset_class = appfilters.Zmmr3010ReportFilter
    template_name = "common/generic-list.html"
    context_object_name = "report"
    permission_required = ["recon.view_zmmr3010reportmodel"]

    def get_queryset(self):
        queryset = self.model.objects.filter(
            Q(is_deleted=False) & ~Q(status=CRS.CLOSED)
        ).order_by("-dt_created")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "ZMMR3010 Reports"
        return context


class Zmmr3010ReportDeleteView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    model = models.Zmmr3010ReportModel
    template_name = "recon/zmmr3010-delete-confirm.html"
    fields = ["is_deleted"]
    success_url = reverse_lazy("recon:zmmr3010_list")
    permission_required = ["recon.delete_zmmr3010reportmodel"]

    def form_valid(self, form):
        form.instance.is_deleted = True
        return super().form_valid(form)


class Zmmr3010ReportCreateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    CreateView,
):
    model = models.Zmmr3010ReportModel
    form_class = appforms.Zmmr3010ReportCreateForm
    template_name = "recon/zmmr3010-create.html"
    form_object = None
    permission_required = ["recon.add_zmmr3010reportmodel"]

    def get_success_url(self):
        if self.form_object:
            return reverse("recon:zmmr3010_load", kwargs={"pk": self.form_object.pk})
        return reverse("recon:zmmr3010_list")

    def form_valid(self, form):
        record = form.save(commit=False)
        record.user_created = self.request.user
        record.status = CRS.NEW
        record.save()
        self.form_object = record
        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Invalid field({field}): {error}")
        return super().form_invalid(form)


class Zmmr3010ReportUpdateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    model = models.Zmmr3010ReportModel
    form_class = appforms.Zmmr3010ReportUpdateForm
    template_name = "recon/zmmr3010-update.html"
    permission_required = ["recon.change_zmmr3010reportmodel"]

    def get_success_url(self):
        return reverse("recon:zmmr3010_list")

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Invalid field({field}): {error}")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update ZMMR3010 Report"
        task = AsyncResult(self.object.task_id)
        context["task"] = task
        try:
            # This is quickfix to handle if no task was set
            _ = task.state
        except ValueError:
            context["task"] = ""
        return context


class LeadingOrderFileUploadListView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    SingleTableMixin,
    FilterView,
):
    model = models.LeadingOrderFileUploadModel
    table_class = apptables.LeadingOrderFileUploadActionTable
    filterset_class = appfilters.LeadingOrderFileUploadFilter
    template_name = "common/generic-list.html"
    permission_required = ["recon.view_leadingorderfileuploadmodel"]

    def get_queryset(self):
        queryset = self.model.objects.filter(
            Q(is_deleted=False) & ~Q(status=CRS.CLOSED)
        ).order_by("-dt_created")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Leading Order File Uploads"
        return context


class LeadingOrderFileUploadCreateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    CreateView,
):
    model = models.LeadingOrderFileUploadModel
    form_class = appforms.LeadingOrderFileUploadCreateForm
    template_name = "recon/leadingorder-fileupload.html"
    form_object = None
    permission_required = ["recon.add_leadingorderfileuploadmodel"]

    def get_success_url(self):
        if self.form_object:
            return reverse(
                "recon:lo_fileupload_load", kwargs={"pk": self.form_object.pk}
            )
        return reverse("recon:lo_fileupload_list")

    def form_valid(self, form):
        record = form.save(commit=False)
        record.user_created = self.request.user
        record.status = CRS.NEW
        record.save()
        self.form_object = record
        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Invalid field({field}): {error}")
        return super().form_invalid(form)


class LeadingOrderFileUploadUpdateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    model = models.LeadingOrderFileUploadModel
    form_class = appforms.LeadingOrderFileUploadUpdateForm
    template_name = "recon/zmmr3010-update.html"
    permission_required = ["recon.change_leadingorderfileuploadmodel"]

    def get_success_url(self):
        return reverse("recon:zmmr3010_list")

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Invalid field({field}): {error}")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update LeadingOrder FileUpload"
        task = AsyncResult(self.object.task_id)
        context["task"] = task
        try:
            # This is quickfix to handle if no task was set
            _ = task.state
        except ValueError:
            context["task"] = ""
        return context


class LeadingOrderTransformCreateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    TemplateView,
):
    model = models.LeadingOrderTransformModel
    permission_required = ["recon.add_leadingordertransformmodel"]
    template_name = "recon/task-create.html"

    def post(self, request, *args, **kwargs):
        obj = models.LeadingOrderTransformModel()
        obj.user_created = request.user
        obj.status = CRS.QUEUED
        obj.save()
        pk_str = str(obj.pk)
        lg.info(f"Queueing task for LeadingOrderTransformModel with {pk_str=}")
        tasks.transform_leadingorder.apply_async((pk_str,), countdown=0)
        messages.success(
            request,
            f"LeadingOrderTransformTask({obj.pk}) has been successfully queued.",
        )
        return redirect(reverse("recon:lo_transform_list"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Are you sure you want to transform Leading Orders?"
        return context


class LeadingOrderTransformListView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    SingleTableView,
):
    model = models.LeadingOrderTransformModel
    table_class = apptables.LeadingOrderTransformTable
    template_name = "common/generic-list.html"
    permission_required = ["recon.view_leadingordertransformmodel"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "LeadingOrder Transform Tasks"
        return context

    def get_queryset(self):
        queryset = self.model.objects.filter(Q(is_deleted=False)).order_by(
            "-dt_created"
        )
        return queryset


class SalesFileUploadListView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    SingleTableMixin,
    FilterView,
):
    model = models.SalesFileUploadModel
    table_class = apptables.SalesFileUploadActionTable
    filterset_class = appfilters.SalesFileUploadFilter
    template_name = "recon/sales-fileupload-list.html"
    permission_required = ["recon.view_salesfileuploadmodel"]

    def get_queryset(self):
        queryset = self.model.objects.filter(
            Q(is_deleted=False) & ~Q(status=CRS.CLOSED)
        ).order_by("-dt_created")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Sales File Uploads"
        return context


class SalesFileUploadCreateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    CreateView,
):
    model = models.SalesFileUploadModel
    form_class = appforms.SalesFileUploadCreateForm
    template_name = "recon/sales-fileupload.html"
    form_object = None
    permission_required = ["recon.add_salesfileuploadmodel"]

    def get_success_url(self):
        if self.form_object:
            return reverse(
                "recon:sales_fileupload_load", kwargs={"pk": self.form_object.pk}
            )
        return reverse("recon:sales_fileupload_list")

    def form_valid(self, form):
        record = form.save(commit=False)
        record.user_created = self.request.user
        record.status = CRS.NEW
        record.save()
        self.form_object = record
        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Invalid field({field}): {error}")
        return super().form_invalid(form)


class SalesFileUploadUpdateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    model = models.SalesFileUploadModel
    form_class = appforms.SalesFileUploadUpdateForm
    template_name = "recon/sales-update.html"
    permission_required = ["recon.change_salesfileuploadmodel"]

    def get_success_url(self):
        return reverse("recon:sales_list")

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Invalid field({field}): {error}")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Sales FileUpload"
        task = AsyncResult(self.object.task_id)
        context["task"] = task
        try:
            # This is quickfix to handle if no task was set
            _ = task.state
        except ValueError:
            context["task"] = ""
        return context


class SalesTransformCreateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    TemplateView,
):
    model = models.SalesTransformModel
    permission_required = ["recon.add_salestransformmodel"]
    template_name = "recon/task-create.html"

    def post(self, request, *args, **kwargs):
        obj = models.SalesTransformModel()
        obj.user_created = request.user
        obj.status = CRS.QUEUED
        obj.save()
        pk_str = str(obj.pk)
        lg.info(f"Queueing task for SalesTransformModel with {pk_str=}")
        tasks.transform_sales.apply_async((pk_str,), countdown=0)
        messages.success(
            request,
            f"SalesTransformTask({obj.pk}) has been successfully queued.",
        )
        return redirect(reverse("recon:sales_transform_list"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Are you sure you want to transform Sales?"
        return context


class SalesTransformListView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    SingleTableView,
):
    model = models.SalesTransformModel
    table_class = apptables.SalesTransformTable
    template_name = "common/generic-list.html"
    permission_required = ["recon.view_salestransformmodel"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Sales Transform Tasks"
        return context

    def get_queryset(self):
        queryset = self.model.objects.filter(Q(is_deleted=False)).order_by(
            "-dt_created"
        )
        return queryset


class OpsFileUploadListView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    SingleTableMixin,
    FilterView,
):
    model = models.OpsFileUploadModel
    table_class = apptables.OpsFileUploadActionTable
    filterset_class = appfilters.OpsFileUploadFilter
    template_name = "recon/ops-fileupload-list.html"
    permission_required = ["recon.view_opsfileuploadmodel"]

    def get_queryset(self):
        queryset = self.model.objects.filter(
            Q(is_deleted=False) & ~Q(status=CRS.CLOSED)
        ).order_by("-dt_created")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Ops File Uploads"
        return context


class OpsFileUploadCreateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    CreateView,
):
    model = models.OpsFileUploadModel
    form_class = appforms.OpsFileUploadCreateForm
    template_name = "recon/ops-fileupload.html"
    form_object = None
    permission_required = ["recon.add_opsfileuploadmodel"]

    def get_success_url(self):
        if self.form_object:
            return reverse(
                "recon:ops_fileupload_load", kwargs={"pk": self.form_object.pk}
            )
        return reverse("recon:ops_fileupload_list")

    def form_valid(self, form):
        record = form.save(commit=False)
        record.user_created = self.request.user
        record.status = CRS.NEW
        record.save()
        self.form_object = record
        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Invalid field({field}): {error}")
        return super().form_invalid(form)


class OpsFileUploadUpdateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    model = models.OpsFileUploadModel
    form_class = appforms.OpsFileUploadUpdateForm
    template_name = "recon/ops-update.html"
    permission_required = ["recon.change_opsfileuploadmodel"]

    def get_success_url(self):
        return reverse("recon:ops_list")

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Invalid field({field}): {error}")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Ops FileUpload"
        task = AsyncResult(self.object.task_id)
        context["task"] = task
        try:
            # This is quickfix to handle if no task was set
            _ = task.state
        except ValueError:
            context["task"] = ""
        return context


class OpsTransformCreateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    TemplateView,
):
    model = models.OpsTransformModel
    permission_required = ["recon.add_opstransformmodel"]
    template_name = "recon/task-create.html"

    def post(self, request, *args, **kwargs):
        obj = models.OpsTransformModel()
        obj.user_created = request.user
        obj.status = CRS.QUEUED
        obj.save()
        pk_str = str(obj.pk)
        lg.info(f"Queueing task for OpsTransformModel with {pk_str=}")
        tasks.transform_ops.apply_async((pk_str,), countdown=0)
        messages.success(
            request,
            f"OpsTransformTask({obj.pk}) has been successfully queued.",
        )
        return redirect(reverse("recon:ops_transform_list"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Are you sure you want to transform Ops?"
        return context


class OpsTransformListView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    SingleTableView,
):
    model = models.OpsTransformModel
    table_class = apptables.OpsTransformTable
    template_name = "common/generic-list.html"
    permission_required = ["recon.view_opstransformmodel"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Ops Transform Tasks"
        return context

    def get_queryset(self):
        queryset = self.model.objects.filter(Q(is_deleted=False)).order_by(
            "-dt_created"
        )
        return queryset
