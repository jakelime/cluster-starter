from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from recon.etl.django.leadingorders import transform as lo_transform
from recon.etl.django.sales.extract import main_example as sales_extract
from recon.etl.django.ops.extract import main_example as ops_extract
from recon.etl.core import utils
from pathlib import Path

MGDB_CONNX = settings.MGDB_CONNECTION_STR

User = get_user_model()


class Command(BaseCommand):
    def transform_leading_orders(self):
        """Transform leading orders data."""
        lo_transform.transform()

    def extract_sales_data(self):
        """Extract sales data."""
        fpath = utils.get_resource_file("engines-sales-*.xlsm", cwd=Path.cwd().parent)
        sales_extract(conn_str=MGDB_CONNX, input_fpath=fpath)

    def extract_ops_data(self):
        """Extract operations data."""
        fpath = utils.get_resource_file("engines-ops-*.xlsx", cwd=Path.cwd().parent)
        ops_extract(conn_str=MGDB_CONNX, input_fpath=fpath)

    def handle(self, *args, **options):
        # self.extract_sales_data()
        self.extract_ops_data()