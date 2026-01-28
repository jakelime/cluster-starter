# recon/enums.py
from django.db import models


class ChoicesReportStatus(models.TextChoices):
    NEW = "NEW"
    DONE = "DONE"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    NONE = "NONE"
    CLOSED = "CLOSED"
    FAILED = "FAILED"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
