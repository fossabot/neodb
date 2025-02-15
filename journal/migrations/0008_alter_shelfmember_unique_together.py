# Generated by Django 3.2.16 on 2023-01-23 05:05

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0002_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("journal", "0007_alter_collection_catalog_item"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="shelfmember",
            unique_together={("owner", "item")},
        ),
    ]
