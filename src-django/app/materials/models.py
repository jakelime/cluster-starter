# materials/models.py
from django.db import models


# Create your models here.
class EnginePartShortageBatch(models.Model):
    external_id = models.CharField(max_length=32, blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)
    df_type = models.CharField(max_length=32, blank=True, null=True)
    esn = models.CharField(max_length=32, blank=True, null=True)
    input_file_date = models.DateField(blank=True, null=True)
    input_filename = models.CharField(max_length=255, blank=True, null=True)
    reportname = models.CharField(max_length=64, blank=True, null=True)
    raw_metadata = models.JSONField(blank=True, null=True)


class EnginePartShortage(models.Model):
    batch = models.ForeignKey(
        EnginePartShortageBatch, on_delete=models.CASCADE, related_name="items"
    )

    part_no = models.CharField(max_length=128, blank=True, null=True)
    descr = models.CharField(max_length=128, blank=True, null=True)
    sort_str = models.CharField(max_length=32, blank=True, null=True)
    qty_engine_job_requiring = models.IntegerField(blank=True, null=True)
    qty_total_shortage = models.IntegerField(blank=True, null=True)
    qty_dues_in = models.IntegerField(blank=True, null=True)
    esn = models.CharField(max_length=32, blank=True, null=True)
    qty_shortage_engine = models.IntegerField(blank=True, null=True)

    # Storage/location numeric codes (use FloatField; normalize NaN > None)
    FV = models.FloatField(blank=True, null=True)
    FVB = models.FloatField(blank=True, null=True)
    GCDR = models.FloatField(blank=True, null=True)
    GH = models.FloatField(blank=True, null=True)
    GHA = models.FloatField(blank=True, null=True)
    GHN = models.FloatField(blank=True, null=True)
    GHP = models.FloatField(blank=True, null=True)
    GHR = models.FloatField(blank=True, null=True)
    GHRN = models.FloatField(blank=True, null=True)
    GLS = models.FloatField(blank=True, null=True)
    GPS = models.FloatField(blank=True, null=True)
    GR = models.FloatField(blank=True, null=True)
    GSV = models.FloatField(blank=True, null=True)
    GV = models.FloatField(blank=True, null=True)
    GVA = models.FloatField(blank=True, null=True)
    GVJT = models.FloatField(blank=True, null=True)
    GVMN = models.FloatField(blank=True, null=True)
    GVNS = models.FloatField(blank=True, null=True)
    GVR = models.FloatField(blank=True, null=True)
