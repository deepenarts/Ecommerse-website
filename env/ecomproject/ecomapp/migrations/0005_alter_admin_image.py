# Generated by Django 4.2.6 on 2023-11-04 02:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecomapp', '0004_remove_admin_address_remove_admin_joined_on_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='admin',
            name='image',
            field=models.ImageField(default='/images/admin.png', upload_to='admins'),
        ),
    ]