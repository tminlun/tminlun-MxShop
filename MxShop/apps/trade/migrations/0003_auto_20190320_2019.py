# Generated by Django 2.0.2 on 2019-03-20 20:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trade', '0002_auto_20190319_2257'),
    ]

    operations = [
        migrations.RenameField(
            model_name='shoppingcart',
            old_name='goods_nums',
            new_name='nums',
        ),
    ]
