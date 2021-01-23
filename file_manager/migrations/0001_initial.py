# Generated by Django 3.1 on 2020-10-03 04:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first', models.CharField(max_length=100)),
                ('last', models.CharField(max_length=100)),
                ('phone', models.CharField(max_length=100)),
                ('email', models.CharField(max_length=100)),
                ('street', models.CharField(max_length=100)),
                ('apt_suite_other', models.CharField(max_length=100)),
                ('city', models.CharField(max_length=100)),
                ('state', models.CharField(max_length=100)),
                ('zip_code', models.CharField(max_length=15)),
            ],
        ),
        migrations.CreateModel(
            name='RentalOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice', models.CharField(max_length=6)),
                ('date', models.DateField(verbose_name='date')),
                ('lg_boxes', models.IntegerField(default=0)),
                ('xl_boxes', models.IntegerField(default=0)),
                ('lg_dollies', models.IntegerField(default=0)),
                ('xl_dollies', models.IntegerField(default=0)),
                ('wardrobes', models.IntegerField(default=0)),
                ('labels', models.IntegerField(default=0)),
                ('zip_ties', models.IntegerField(default=0)),
                ('bins', models.IntegerField(default=0)),
                ('rental_period', models.CharField(max_length=100)),
                ('delivery_date', models.DateField(verbose_name='delivery date')),
                ('delivery_street', models.CharField(max_length=100)),
                ('delivery_apt_suite_other', models.CharField(max_length=100)),
                ('delivery_city', models.CharField(max_length=100)),
                ('delivery_state', models.CharField(max_length=100)),
                ('delivery_zip_code', models.CharField(max_length=15)),
                ('pickup_date', models.DateField(verbose_name='pickup date')),
                ('total_price', models.FloatField(default=0)),
                ('pickup_address', models.CharField(max_length=100)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='file_manager.customer')),
            ],
        ),
    ]
