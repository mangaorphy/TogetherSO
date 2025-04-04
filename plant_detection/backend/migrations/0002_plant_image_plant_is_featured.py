# Generated by Django 5.1.6 on 2025-03-11 14:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="plant",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to="plants/"),
        ),
        migrations.AddField(
            model_name="plant",
            name="is_featured",
            field=models.BooleanField(default=False),
        ),
    ]
