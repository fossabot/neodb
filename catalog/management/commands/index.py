from django.core.management.base import BaseCommand
from django.conf import settings
from catalog.models import *
import pprint
from django.core.paginator import Paginator
from tqdm import tqdm
from time import sleep
from datetime import timedelta
from django.utils import timezone

BATCH_SIZE = 1000


class Command(BaseCommand):
    help = "Manage the search index"

    def add_arguments(self, parser):
        parser.add_argument(
            "--init",
            help="initialize index",
            action="store_true",
        )
        parser.add_argument(
            "--update",
            help="update index schema",
            action="store_true",
        )
        parser.add_argument(
            "--stat",
            action="store_true",
        )
        parser.add_argument(
            "--reindex",
            action="store_true",
        )

    def init_index(self):
        Indexer.init()
        self.stdout.write(self.style.SUCCESS("Index created."))

    def update_index(self):
        Indexer.update_settings()
        self.stdout.write(self.style.SUCCESS("Index updated."))

    def stat(self, *args, **options):
        stats = Indexer.get_stats()
        pprint.pp(stats)

    def reindex(self):
        if Indexer.busy():
            self.stdout.write("Please wait for previous updates")
        # Indexer.update_settings()
        # self.stdout.write(self.style.SUCCESS('Index settings updated.'))
        qs = Item.objects.filter(
            is_deleted=False
        )  # if h == 0 else c.objects.filter(edited_time__gt=timezone.now() - timedelta(hours=h))
        pg = Paginator(qs.order_by("id"), BATCH_SIZE)
        for p in tqdm(pg.page_range):
            items = list(
                map(
                    lambda o: Indexer.obj_to_dict(o),
                    [
                        x
                        for x in pg.get_page(p).object_list
                        if x.__class__ != CatalogCollection
                    ],
                )
            )
            if items:
                Indexer.replace_batch(items)
                while Indexer.busy():
                    sleep(0.5)

    def handle(self, *args, **options):
        if options["init"]:
            self.init_index()
        elif options["update"]:
            self.update_index()
        elif options["stat"]:
            self.stat()
        elif options["reindex"]:
            self.reindex()
        # else:

        # try:
        #     Indexer.init()
        #     self.stdout.write(self.style.SUCCESS('Index created.'))
        # except Exception:
        #     Indexer.update_settings()
        #     self.stdout.write(self.style.SUCCESS('Index settings updated.'))
