# Generated by Django 3.1.5 on 2022-04-01 01:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('file_manager', '0003_item_itemtype_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='rentalorder',
            name='handtrucks',
            field=models.IntegerField(default=0),
        ),
    ]