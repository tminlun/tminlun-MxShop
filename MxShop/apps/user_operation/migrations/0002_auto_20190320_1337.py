# Generated by Django 2.0.2 on 2019-03-20 13:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_operation', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useraddress',
            name='signer_mobile',
            field=models.CharField(blank=True, default='', max_length=11, null=True, verbose_name='收货人手机'),
        ),
    ]
