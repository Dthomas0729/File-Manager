# Generated by Django 3.1.5 on 2022-02-19 02:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('file_manager', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rentalorder',
            name='wardrobes',
        ),
        migrations.RemoveField(
            model_name='rentalorder',
            name='xl_dollies',
        ),
    ]
